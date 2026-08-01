"""decision-map phase-2 probe -- GitHub half (ADR 0059 gate, result in ADR 0060).

Settles the one bet the tracker design rests on: does a
`<!-- decision-map:key:<key> -->` marker written into an issue body survive
round trips through the API, a close/reopen, and (human step) the web-UI editor?

    python probe_tracker_github.py <owner/repo> --yes

THIS SCRIPT CREATES REAL ISSUES and does not delete them (issues cannot be
deleted through the REST API). Point it at a THROWAWAY PRIVATE repo -- never at
a repo anyone reads. It refuses to run without --yes for that reason.

Writes probe-verdict.json to the current directory. Step 3 (edit the body in the
web UI, then re-fetch) is a human step: the script prints the URL and leaves the
issue open for it.

Result of the 2026-08-01 run: examples/probe-verdict-github-2026-08-01.json
"""
import io
import json
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

args = [a for a in sys.argv[1:] if not a.startswith('-')]
flags = {a for a in sys.argv[1:] if a.startswith('-')}

if not args or '--yes' not in flags:
    print(__doc__)
    print('refusing to run: pass a target repo and --yes.')
    raise SystemExit(2)

REPO = args[0]

MARK_OK = '<!-- decision-map:key:auth-model -->'
MARK_DD = '<!-- decision-map:key:foo--bar -->'
FOG_OPEN = '<!-- decision-map:fog:start -->'
FOG_CLOSE = '<!-- decision-map:fog:end -->'
FORGE = 'Auth <!-- decision-map:key:injected --> model'

results = {}
created = []


def gh(*args, body=None):
    p = subprocess.run(['gh', *args], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', input=body)
    return p.returncode, p.stdout, p.stderr


def gh_json(*args, body=None):
    rc, out, err = gh(*args, body=body)
    if rc != 0:
        return None, err.strip()
    try:
        return json.loads(out), None
    except json.JSONDecodeError:
        return out.rstrip('\n'), None


def record(step, passed, detail, extra=None):
    results[step] = {'pass': passed, 'detail': detail}
    if extra:
        results[step].update(extra)
    flag = 'PASS' if passed else ('TODO' if passed is None else 'FAIL')
    print(f"[{flag}] {step}: {detail}")


def make_issue(title, body):
    data, err = gh_json('api', f'repos/{REPO}/issues', '-X', 'POST',
                        '-f', f'title={title}', '-f', f'body={body}')
    if err:
        return None, err
    created.append(data['number'])
    return data, None


def get_body(num):
    # Fetch the whole object and index it in Python. Going through `--jq .body`
    # returns a bare string that jq terminates with a newline, and stripping that
    # newline back off silently corrupts a byte-comparison of the body's tail --
    # it reported a false "GitHub strips the trailing newline" on the first run.
    data, err = gh_json('api', f'repos/{REPO}/issues/{num}')
    if err:
        return '', err
    return (data or {}).get('body') or '', None


# ---------------------------------------------------------------- step 1
body1 = f"Question\n\n{MARK_OK}\n\n{FOG_OPEN}\n- one\n- two\n{FOG_CLOSE}\n"
iss1, err = make_issue('probe: marker round-trip', body1)
if err:
    record('1-marker-roundtrip', False, f'create failed: {err[:300]}')
else:
    got, gerr = get_body(iss1['number'])
    exact = got == body1
    has_marker = MARK_OK in got
    record('1-marker-roundtrip', has_marker,
           f"marker present={has_marker}; whole body byte-identical={exact}",
           {'issue': iss1['number'], 'sent_len': len(body1), 'got_len': len(got),
            'sent_repr': repr(body1), 'got_repr': repr(got)})

# ---------------------------------------------------------------- step 2
body2 = f"Question\n\n{MARK_DD}\n"
iss2, err = make_issue('probe: double-hyphen key', body2)
if err:
    record('2-double-hyphen-key', False, f'create failed: {err[:300]}')
else:
    got, _ = get_body(iss2['number'])
    survives = MARK_DD in got
    record('2-double-hyphen-key', True,
           f"`--` marker survives the API verbatim={survives}",
           {'issue': iss2['number'], 'survived_api': survives, 'got_repr': repr(got)})

# ---------------------------------------------------------------- step 4
if iss1:
    n = iss1['number']
    gh('api', f'repos/{REPO}/issues/{n}', '-X', 'PATCH', '-f', 'state=closed')
    gh('api', f'repos/{REPO}/issues/{n}', '-X', 'PATCH', '-f', 'state=open')
    got, _ = get_body(n)
    record('4-close-reopen', MARK_OK in got,
           f"marker present after close+reopen={MARK_OK in got}; "
           f"body byte-identical={got == body1}")

# ---------------------------------------------------------------- forging
iss3, err = make_issue(FORGE, f"Question\n\n{MARK_OK}\n")
if err:
    record('X-key-forging', False, f'create failed: {err[:300]}')
else:
    title, _ = gh_json('api', f'repos/{REPO}/issues/{iss3["number"]}', '--jq', '.title')
    got, _ = get_body(iss3['number'])
    record('X-key-forging', True,
           f"title stored verbatim with a forged marker in it: {'injected' in str(title)}; "
           f"key markers in body={got.count('<!-- decision-map:key:')}",
           {'issue': iss3['number'], 'title': title})

# ---------------------------------------------------------------- step 6
if iss1:
    sub, sub_err = gh_json('api', f'repos/{REPO}/issues/{iss1["number"]}/sub_issues')
    if sub_err:
        record('6a-sub-issues-list', False, f'GET sub_issues failed: {sub_err[:300]}')
    else:
        record('6a-sub-issues-list', True,
               f'GET sub_issues OK, {len(sub) if isinstance(sub, list) else "?"} items')

if iss1 and iss2:
    child_id, _ = gh_json('api', f'repos/{REPO}/issues/{iss2["number"]}', '--jq', '.id')
    rc, out, err = gh('api', f'repos/{REPO}/issues/{iss1["number"]}/sub_issues',
                      '-X', 'POST', '-F', f'sub_issue_id={child_id}')
    ok = rc == 0
    record('6b-sub-issues-add', ok,
           'POST sub_issues OK' if ok else f'POST failed: {err.strip()[:300]}',
           {'parent': iss1['number'], 'child': iss2['number'], 'child_id': child_id})
    if ok:
        lst, _ = gh_json('api', f'repos/{REPO}/issues/{iss1["number"]}/sub_issues',
                         '--jq', '[.[].number]')
        record('6c-sub-issues-enumerate', True, f'children enumerated: {lst}',
               {'children': lst})

# ---------------------------------------------------------------- dependencies
if iss1:
    rc, out, err = gh('api', f'repos/{REPO}/issues/{iss1["number"]}/dependencies/blocked_by')
    record('D-blocked-by-api', rc == 0,
           f'native blocked_by endpoint responds: {out.strip()[:120]}' if rc == 0
           else f'no native blocked_by: {err.strip()[:200]}')

# ---------------------------------------------------------------- step 3 setup
if iss1:
    results['3-webui-edit'] = {
        'pass': None,
        'detail': 'HUMAN STEP -- edit the body in the web UI, save, then re-check the marker.',
        'url': f'https://github.com/{REPO}/issues/{iss1["number"]}',
        'expect_marker': MARK_OK,
    }
    print(f"[TODO] 3-webui-edit: open {results['3-webui-edit']['url']} and edit the body in a browser.")

results['_meta'] = {'repo': REPO, 'created_issues': created}
with open('probe-verdict.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nwrote probe-verdict.json ({len(created)} issues created: {created})")
