---
name: content-publishing
description: Publish to 小红书/知乎/抖音 with verify-before-claim.
version: 2.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [social-media, publishing, xiaohongshu, zhihu, douyin]
    related_skills: [social-media-automation, douyin-shortform, verification-before-completion]
    pinned: true
---

# Content Publishing

> **Canonical path — prefer these exact steps over untested alternatives.** The
> facts below are verified working. If a publish attempt fails, fix the *step*; do
> not conclude a tool is broken and re-add QR / sandbox-Playwright / xhs-library
> dead ends. `browser_upload` exists and works.

The ONE canonical way to publish to 小红书 (Xiaohongshu), 知乎 (Zhihu), and 抖音
(Douyin), using the persistent, already-logged-in browser session. Requires
positive evidence a post went live before you may say it was published.

## When to Use

Any time you publish, upload, or submit content to 小红书 / 知乎 / 抖音 — a note,
an answer, or a video. Use it for the upload step and for confirming the result.

## Do Not Reinvent

There is exactly **one** upload path per platform: the logged-in browser session
+ the `browser_upload` tool. Before anything else:

- **`browser_upload` uploads** 抖音 videos and 小红书 covers in the SAME logged-in
  session (Playwright `setInputFiles` / drag-drop behind the browser tool).
- **Do NOT** launch a fresh sandbox Playwright / headless Chromium.
- **Do NOT** re-scan a QR code — all three platforms are already logged in. Only
  fall back to QR if a verification step PROVES the session is logged out.
- **Do NOT** write throwaway `publish_*.py` / `*_qr_upload.py` / `*_login.py`
  scripts, and do NOT use the `xhs` library / API-sign hacks. The browser tools
  do the work.
- If a step fails, fix that step — never switch approaches mid-stream.

## Prerequisites

- A logged-in browser session reachable by the `browser_*` tools (all three
  accounts share one logged-in profile).
- The content file(s) exist (e.g. `/root/hermes-content/<platform>/...`). Make
  videos with the **douyin-shortform** skill first.

## How to Run

The loop for every platform:

1. `browser_navigate` to the platform's create/upload page.
2. `browser_snapshot` to see the page + get element refs.
3. Fill text with `browser_type`; upload media with `browser_upload`.
4. Click 发布 / 提交 (`browser_click`, or the per-platform publish tool below).
5. **Verify-before-claim** (mandatory — see below).
6. Report the result with evidence.

## Quick Reference

| Tool | Use in publishing |
|------|-------------------|
| `browser_navigate` | Open the create/upload page |
| `browser_snapshot` | Read page + get element refs |
| `browser_upload` | Set file(s) on a `<input type=file>` (video/cover) |
| `browser_type` | Title / description / answer body |
| `browser_click` | Click 发布 / 创作 / 提交 |
| `browser_console` (expression=) | Read `location.href` / DOM to VERIFY publish |
| `browser_vision` | Screenshot proof of the published state |

**`browser_upload` usage — PICK THE MODE BY PLATFORM (this is where past attempts went wrong):**
- Args: `file_paths=[...]`, plus a target: `selector`/`ref` (the `<input type=file>`),
  `click_ref`/`click_selector` (a visible button → native chooser), or `drop=true`.
- **🎵 抖音 video → `browser_upload(file_paths=["<the mp4>"], selector="input[type=file]", verify_text=["上传中","转码中","重新上传"])`.**
  `setInputFiles` works on the hidden input — no QR, no native dialog. The
  `verify_text` markers make the tool CONFIRM the SPA accepted the file and return
  `bound:true/false` — **trust that flag**: `bound:false` → re-navigate to a fresh
  upload page and retry ONCE with `drop=true` (same `verify_text`); still false →
  report 「上传未绑定」 honestly.
- **⛔ 📕 小红书 图文 (image notes) → `browser_upload(file_paths=[...], drop=true)` —
  MANDATORY; the normal mode SILENTLY FAILS.** 小红书's uploader only reacts to a
  drag-drop `DataTransfer` and IGNORES `input.files`/`setInputFiles`, so a plain
  `selector` upload returns `success:true` but the editor stays EMPTY. `drop=true`
  opens the 图片编辑 editor with the image (verified). NEVER use plain `selector`
  for 小红书 images; NEVER use `drop=true` for 抖音 video.
- Fallback (抖音 only, if a direct selector truly fails): `click_selector`/`click_ref`
  of the visible upload button (filechooser path).
- The error message tells you how to fix it (it lists the files that actually exist
  + what to do). Read it and adjust — do NOT conclude the tool is broken.

> 🧠 **How file upload works (container/host — already solved, do not re-derive).**
> `browser_upload` ships the file's BYTES (base64) to the browser server, which
> writes them next to the browser and does `setInputFiles` there — **no host path
> is ever sent to the browser/CDP**, so a file inside a container uploads fine.
> - **Pass the CONTAINER path** (e.g. `/root/hermes-content/douyin/x.mp4`). It is
>   auto-translated to the real host file. Do NOT invent a host path that does not
>   exist — that is the classic cause of "upload failed."
> - Do NOT install a browser in the sandbox, do NOT spawn sandbox Playwright, do
>   NOT re-scan QR "because the file can't reach the browser." It already can.

## Procedure

### 抖音 (video)
1. `browser_navigate` → `https://creator.douyin.com/creator-micro/content/upload`.
2. `browser_snapshot`.
3. **Upload WITH binding verification** (a mechanically-ok injection is NOT proof —
   抖音's uploader sometimes ignores it entirely):
   `browser_upload(file_paths=["/root/hermes-content/douyin/<video>.mp4"], selector="input[type=file]", verify_text=["上传中","转码中","重新上传"])`.
   The result carries **`bound:true/false`**:
   - `bound:true` → the video registered; continue.
   - `bound:false` → the file did NOT enter the form. **Do NOT fill the form.**
     Re-`browser_navigate` to a fresh upload page and retry ONCE (last resort
     `drop=true`, same `verify_text`). Still `bound:false` → report 「上传未绑定」
     honestly and stop.
   ⚠️ The 作品描述/发布 form rendering alone is NOT proof the video bound — 抖音 renders
   that chrome even with an empty form (this caused the old draft-only failures).
4. **Wait for the upload to FINISH** — re-`browser_snapshot` until there is no
   上传中/转码中/百分比 progress and the 发布 button is enabled.
5. `browser_type` the title and description (+ hashtags); set a cover if offered
   (the pipeline exports a designed `<video>.cover.jpg` next to the mp4 — 封面 input
   only accepts jpg/png).
6. **Publish with `browser_douyin_publish(title="<the exact title you typed>")`** — NOT
   a bare `browser_click` 发布. It waits for upload/transcode AND the content pre-check
   (auto-clicking 重新检测, retrying 发布 through 「检测人数过多」 busy toasts),
   trusted-clicks 发布, then CONFIRMS the post is actually listed in 作品管理 (a 发布成功
   toast / the editor URL renaming is NOT proof). It returns one of:
   - `published:true` → confirmed live in 作品管理 (审核中 counts) → report 已发布.
   - `needsVerify:true` → an SMS/captcha 风控 wall: report 「未确认发布:抖音需短信验证,
     需用户处理」 + screenshot. Do NOT loop or fake success.
   - `reason:"detection_busy"` → 抖音's content pre-check is overloaded; the draft is
     safe on the page. Run `sleep 420` in the terminal, then call
     `browser_douyin_publish` ONCE more. Still busy → report 「未确认发布:检测过载,
     草稿已存」 and stop. **Max 2 publish calls total — never loop beyond that.**
   - other `unconfirmed:true` → clicked but NOT in 作品管理 → report 「未确认发布」,
     never 已发布.
7. Verify (below): for 抖音 the ONLY proof is the post showing in 作品管理.

### 小红书 (image note 图文) — verified end-to-end working
0. **Build quality cards FIRST (do NOT post a bare AI image — 小红书 is cover-driven).**
   Write a spec JSON `{title, subtitle, tag, cards:[{heading,body},...], bg?}` (content
   per **social-media-automation**: one insight, specific, human) and run the locked
   script (it lives in the douyin-shortform skill's scripts):
   `python "$(find ~/.hermes/skills -name make_xhs_cards.py|head -1)" --spec spec.json --outdir /root/hermes-content/小红书/<date>-<topic>`
   → `01-cover.png` (designed cover) + `02..-card.png` (干货 carousel). Upload THESE.
1. `browser_navigate` → `https://creator.xiaohongshu.com/publish/publish`.
2. Switch to the **上传图文** tab (default is 上传视频): `browser_click` its ref, or by text
   `browser_console(expression="[...document.querySelectorAll('*')].find(e=>e.children.length===0&&e.textContent.trim()==='上传图文')?.closest('div,button,li,span')?.click()")`.
3. **`browser_upload(file_paths=[all the card PNGs], drop=true)` — `drop=true` is
   MANDATORY.** 小红书's uploader only accepts drag-drop and ignores `setInputFiles`
   (a normal upload returns success but the editor stays EMPTY). `drop=true` opens the
   图片编辑 editor with the images.
4. `browser_type` the title (≤20 chars) and body; add 3-5 topic tags.
5. **发布 — call `browser_xhs_publish()`. One tool, NO coordinates.** 小红书's 发布
   button is a closed-shadow `<xhs-publish-btn>` whose clickable red pill is
   RIGHT-anchored, so computing its center and clicking it MISSES (the old
   "clicked 发布 but nothing happened / looped 5×" bug). `browser_xhs_publish`
   locates + clicks the pill server-side and confirms `/publish/success`; it returns
   `{published: true|false}`.
   - `published: true` → go verify (step 6).
   - `published: false` → do NOT loop-click and do NOT compute coordinates yourself.
     Go straight to 笔记管理 (step 6): if the note is there report 已发布, else 未确认发布.
   - (New 小红书 notes first appear under 审核中 then move to 已发布 — that is normal
     review, NOT a failure. Seeing the note in 笔记管理 at all = 已发布.)
6. Verify (below): 笔记管理 shows the new note (审核中 or 已发布 both count).

### 知乎 (answer) — no file upload
1. `browser_navigate` → `https://www.zhihu.com/question/<id>`.
2. Open the editor: `browser_snapshot`, then `browser_click` the **创作** nav button
   (or **写回答** on the question page) by its ref. If neither is in the snapshot,
   `browser_console(expression="document.querySelector('a[href*=\\"creator\\"]')?.click()")`.
3. `browser_type` the answer into the `[contenteditable]` editor.
4. `browser_click` 发布回答. Verify (below).

### Verify-Before-Claim Gate (the honesty rule)
After clicking 发布/提交, you MUST obtain positive evidence the post is live
BEFORE any 已发布 / ✅ wording:
1. **URL change** — `browser_console(expression="location.href")`: a
   note/answer/video permalink (not the editor URL).
2. **DOM/state** — `browser_snapshot` shows 发布成功 / the new item atop the
   creator content list.
3. **Screenshot** — `browser_vision` of the published state, as proof.

Have URL-change OR DOM-confirmation, AND a screenshot → report 已发布 with the
permalink. **No evidence → report 「未确认发布」 with the screenshot — never claim
已发布.** A fabricated success is a hard failure. This is a publishing instance
of **verification-before-completion**: evidence before done.

> ⛔ **抖音 — 作品管理 is the ONLY authority.** A 发布成功 toast, a satisfaction-survey
> popup, or the editor URL changing (`/content/upload` → `/content/publish?…`) are NOT
> proof — 抖音 renames its own URL, which previously caused FALSE 已发布 reports.
> `browser_douyin_publish`'s `published:true` already means the server SAW the post in
> 作品管理. If you ever click 发布 any other way, you MUST re-load 作品管理 and confirm the
> new dated/titled item appears in 已发布 or 审核中 — if it is not there, report
> 未确认发布 even when the page said 发布成功.

### Idempotency / Resume
Before publishing, check the creator content list / drafts. If the same dated
content is already live, report 「已存在，跳过」 instead of double-posting.

## Reporting

After a confirmed publish:
```
已发布：
- 📕 小红书：「标题」— permalink/截图
- 📗 知乎：「问题」— permalink/截图
- 🎵 抖音：「主题」— permalink/截图
```
Unconfirmed → 「未确认发布：<platform> — <what you saw> + 截图」. Never publish
silently.

## Pitfalls

- The file input is usually hidden behind a styled button — `browser_upload`'s
  `setInputFiles` works on hidden inputs anyway; use `selector="input[type=file]"`.
  No QR, no native dialog needed.
- Never report 已发布 from "I clicked the button" — only from verified evidence.
- If verification shows logged-out, THEN (only then) do a QR re-login.
- **Do NOT message the user on every micro-step.** Messaging bridges rate-limit
  rapid sends, after which your images/QRs stop arriving. Send at most: one status
  at start, one screenshot if needed, one result at the end.

## Verification

A run is correct iff: (1) no throwaway publish script or new QR was created when
a session was live; (2) the final message has a permalink or screenshot for each
platform claimed 已发布; (3) any platform without evidence is reported 未确认发布.
