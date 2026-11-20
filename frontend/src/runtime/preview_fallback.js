/**
 * Safe fallback renderer when WebContainers or iframe preview fails to load.
 */

export function renderFallbackPreview(containerEl, error) {
  if (!containerEl) return;
  containerEl.innerHTML = `
    <div style="padding: 24px; color: #e2e8f0; font-family: sans-serif; text-align: center;">
      <h3 style="color: #f87171; margin-bottom: 8px;">Preview Unavailable</h3>
      <p style="color: #94a3b8; font-size: 14px; max-width: 480px; margin: 0 auto 16px;">
        ${error?.message || "WebContainer environment could not be initialized in this browser session."}
      </p>
      <div style="font-size: 12px; color: #64748b;">
        You can still inspect the generated code in the Monaco Editor or download the project archive.
      </div>
    </div>
  `;
}

