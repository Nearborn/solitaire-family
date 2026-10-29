/* Browser-independent Solitaire input: real canvas coordinates normalized to [0,1]. */
(() => {
  "use strict";
  const queue = [];
  let active = null;
  let canvas = null;
  const maxQueue = 256;

  function enqueue(type, e) {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    const x = Math.min(1.25, Math.max(-0.25, (e.clientX - rect.left) / rect.width));
    const y = Math.min(1.25, Math.max(-0.25, (e.clientY - rect.top) / rect.height));
    queue.push({type, x, y, button: e.button || 0});
    if (queue.length > maxQueue) queue.splice(0, queue.length - maxQueue);
  }
  window.solitaireDrainInput = () => JSON.stringify(queue.splice(0, queue.length));
  window.solitairePointerReady = false;

  function attach() {
    if (window.solitairePointerReady) return;
    canvas = document.getElementById("canvas");
    if (!canvas) return;
    const opts = {capture: true, passive: false};
    canvas.style.touchAction = "none";

    canvas.addEventListener("pointerdown", e => {
      if (active !== null || e.button > 0) return;
      active = e.pointerId;
      try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
      enqueue("down", e);
      e.preventDefault();
      e.stopImmediatePropagation();
    }, opts);

    canvas.addEventListener("pointermove", e => {
      if (active !== null && e.pointerId === active) {
        enqueue("move", e);
        e.preventDefault();
        e.stopImmediatePropagation();
      }
    }, opts);

    const release = e => {
      if (active === null || e.pointerId !== active) return;
      enqueue("up", e);
      active = null;
      try { canvas.releasePointerCapture(e.pointerId); } catch (_) {}
      e.preventDefault();
      e.stopImmediatePropagation();
    };
    canvas.addEventListener("pointerup", release, opts);
    canvas.addEventListener("pointercancel", release, opts);
    window.solitairePointerReady = true;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach, {once: true});
  } else {
    attach();
  }
})();
