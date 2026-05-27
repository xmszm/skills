# Rich-Text Images

Do not download raw `devops.aliyun.com/projex/api/workitem/file/url?...` image
URLs directly with `curl` or a browser request. They can return `invalid
session` even when the image is available through the Yunxiao MCP session.

Both normal attachments and rich-text embedded images should go through the
Yunxiao file tool first:

- Rich-text images use the long hex `fileIdentifier` from `htmlValue` or
  `jsonMLValue`.
- Normal attachments use the numeric attachment ID returned by
  `list_workitem_attachments`.
- Call `get_workitem_file` with the appropriate ID, then download the temporary
  URL returned by that tool immediately.

Video evidence is out of scope for this workflow. If a normal attachment or
rich-text embedded file is a video, do not download or analyze it, do not edit
code, and do not write Yunxiao comments or status updates. Leave the item
unchanged and report it as postponed in the final response.

Treat these as video indicators: MIME type starting with `video/`, file suffix
such as `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`, `.wmv`, `.m4v`, or
Yunxiao file metadata that identifies the file as video.

Best path:

1. Parse work item description/comment rich text with
   `scripts/extract_rich_text_manifest.py`. Do not manually reason over raw
   `htmlValue`, `jsonMLValue`, empty spans, style attributes, or base64 noise.
2. Use the script output as the reading manifest: clean text plus image
   placeholders that include the target local file path.
3. For each image in the manifest, call `get_workitem_file` with
   `organizationId`, `workitemId`, and `id: <fileIdentifier>`.
4. Cache downloaded files at the manifest `path`. By default,
   `scripts/extract_rich_text_manifest.py` uses `system-cache`, resolved to
   the OS cache directory:
   - Windows: `%LOCALAPPDATA%\Codex\yunxiao-workitem\images`
   - macOS: `~/Library/Caches/Codex/yunxiao-workitem/images`
   - Linux: `$XDG_CACHE_HOME/codex/yunxiao-workitem/images` or
     `~/.cache/codex/yunxiao-workitem/images`
   Set `YUNXIAO_WORKITEM_CACHE_DIR` or pass `--cache-root <absolute-path>` only
   when a project needs a different local cache.
5. Download the returned signed OSS `url` immediately after calling
   `get_workitem_file`. Do not collect signed URLs first and download them
   later; these links can expire quickly.
6. If using a downloader pool, queue stable `fileIdentifier` values in FIFO
   order, not signed URLs. Each worker should fetch a fresh URL and download it
   immediately.
7. Prefer `curl --noproxy '*' -sS -L --connect-timeout 5 --max-time 20` when
   downloading OSS URLs from constrained proxy environments.
8. Before downloading, reuse the cached file only when it exists, is non-empty,
   and opens as an image. If it is missing, empty, or invalid, download again
   from a newly returned signed URL.
9. Always validate the downloaded file with `file` or by opening it with the
   image viewer. If the saved file is XML/text and contains `AccessDenied` or
   `Request has expired`, discard it, call `get_workitem_file` again for a
   fresh signed URL, and download immediately.
10. Always re-read current work item description/comments and use only currently
   referenced `fileIdentifier` values. If a screenshot was replaced, Yunxiao
   normally emits a new `fileIdentifier`, so the new image downloads while stale
   cached files are ignored.
11. Open the local image before scoring clarity or editing.

Prefer a manifest-first reading shape after extraction:

- `rawText`: plain text only, with images removed.
- `annotatedText`: model-facing text extracted from Yunxiao rich text with each
  original image position replaced by `{{image:<imageRef> path:<localPath>}}`.
- `images`: a map whose keys match the `<imageRef>` part in `annotatedText`.
  Each value should include `fileIdentifier`, local `path`, `valid`, and cheap
  validation metadata such as `mime` or `bytes`.
- Stable `imageRef` format: use `description-<index>` for description images
  and `comment-<commentId>-<index>` for comment images.
- Do not include signed OSS URLs in the manifest; keep them inside the
  downloader only.

Example manifest fragment:

```json
{
  "annotatedText": "当前弹窗字段跟上图无法对上：\n{{image:comment-20837910-1 path:<system-cache>/RJJV-55/6f368c5f9663cf419f03a9d7b7.png}}\n新增项目后，左下角记录有增加1，但列表中无法找到该条数据：\n{{image:comment-20837910-2 path:<system-cache>/RJJV-55/9cc2a26f7d6244a6b80d16e231.png}}",
  "images": {
    "comment-20837910-1": {
      "fileIdentifier": "6f368c5f9663cf419f03a9d7b7",
      "path": "<system-cache>/RJJV-55/6f368c5f9663cf419f03a9d7b7.png",
      "valid": true,
      "mime": "image/png"
    }
  }
}
```

`list_workitem_attachments` is useful for explicit attachments, but embedded
rich-text images may not appear as attachments. An empty attachment list does
not mean screenshots are unavailable.

Treat direct URL authorization failures as a tool-choice issue, not proof that
the screenshot is inaccessible. If screenshots remain unavailable after
`get_workitem_file`, rely on title plus code evidence only when code has a
precise match.
