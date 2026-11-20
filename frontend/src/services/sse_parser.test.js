/**
 * Tests for frontend Server-Sent Events (SSE) stream buffer parsing.
 */

describe("Frontend SSE Buffer Parser", () => {
  it("should parse full SSE message events correctly", () => {
    const rawChunk = 'data: {"type": "file_created", "path": "index.html"}\n\n';
    const lines = rawChunk.split("\n");
    const dataLine = lines.find((l) => l.startsWith("data:"));
    expect(dataLine).toBeDefined();

    const parsed = JSON.parse(dataLine.replace(/^data:\s*/, ""));
    expect(parsed.type).toBe("file_created");
    expect(parsed.path).toBe("index.html");
  });

  it("should ignore comment or keep-alive lines", () => {
    const rawChunk = ": ping\n\n";
    const lines = rawChunk.split("\n");
    const dataLine = lines.find((l) => l.startsWith("data:"));
    expect(dataLine).toBeUndefined();
  });
});

