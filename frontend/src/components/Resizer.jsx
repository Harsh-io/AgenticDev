import React from "react";

export default function Resizer({
  direction,
  onMouseDown,
  onDoubleClick,
  title = "Drag to resize | Double-click to reset",
}) {
  return (
    <div
      className={`resizer-divider ${direction === "vertical" ? "vertical-bar" : "horizontal-bar"}`}
      onMouseDown={onMouseDown}
      onDoubleClick={onDoubleClick}
      title={title}
      role="separator"
      tabIndex={0}
      aria-orientation={direction === "vertical" ? "vertical" : "horizontal"}
    />
  );
}
