# Zhihu Publishing Notes

知乎 is already logged in in the persistent browser session — **no QR login is
needed**. Publish via the `content-publishing` skill. The only 知乎-specific facts
worth keeping:

- **知乎 blocks headless/sandbox Playwright** (returns `40362 您当前请求存在异常`).
  Always use the logged-in browser session — never a sandbox browser.
- **Open the editor via the `创作` nav button** (more reliable than `写回答`), or
  navigate straight to `https://www.zhihu.com/question/<id>` and click 写回答.
- Type the answer into the `[contenteditable]` editor (`browser_type`), then click
  **发布回答**.
- **Verify-before-claim**: after 发布, confirm with the answer permalink
  (`browser_console(expression="location.href")`) and/or a `browser_snapshot`
  showing 发布成功 before saying 已发布. No evidence → report 未确认发布.
- 知乎 needs **no file upload** — it is text only.

Content shape (length, structure) is in the `social-media-automation` SKILL.
