/**
 * Shared Crop Components
 * 재사용 가능한 크롭 관련 컴포넌트 및 유틸리티
 */

const { useState, useRef, useEffect } = React;

/* ═══════════════════════════════════════════════
   Canvas Helpers
   ═══════════════════════════════════════════════ */

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function fillRR(ctx, x, y, w, h, r, color) {
  roundRect(ctx, x, y, w, h, r);
  ctx.fillStyle = color;
  ctx.fill();
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Image load failed"));
    img.src = src;
  });
}

/* ═══════════════════════════════════════════════
   Button Styles
   ═══════════════════════════════════════════════ */

const btnBlueSm = {
  background: "#3B82F6",
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "8px 16px",
  fontSize: 13,
  fontWeight: 700,
  cursor: "pointer",
};

const btnGraySm = {
  background: "#F1F5F9",
  color: "#64748B",
  border: "none",
  borderRadius: 8,
  padding: "8px 16px",
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
};

/* ═══════════════════════════════════════════════
   Canvas-based CropCanvas Component
   Large display with scrolling - no zoom complexity
   ═══════════════════════════════════════════════ */

function CropCanvas({ imageSrc, pageIdx, onCropDone }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [img, setImg] = useState(null);
  const [drawing, setDrawing] = useState(false);
  const [startPos, setStartPos] = useState(null);
  const [rect, setRect] = useState(null);
  const [canvasSize, setCanvasSize] = useState({ w: 0, h: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // Load image when imageSrc changes
  useEffect(() => {
    if (!imageSrc) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    setImg(null);
    setRect(null);

    const image = new Image();
    image.crossOrigin = "anonymous";

    image.onload = () => {
      console.log("[CropCanvas] Image loaded:", image.naturalWidth, "x", image.naturalHeight);

      // Display at FULL resolution (or slightly scaled if very large)
      // This ensures no coordinate transformation issues
      let w = image.naturalWidth;
      let h = image.naturalHeight;

      // Only scale down if extremely large (> 2000px)
      const maxDim = 2000;
      if (w > maxDim || h > maxDim) {
        const ratio = Math.min(maxDim / w, maxDim / h);
        w = Math.round(w * ratio);
        h = Math.round(h * ratio);
      }

      console.log("[CropCanvas] Canvas size:", w, "x", h);
      setCanvasSize({ w, h });
      setImg(image);
      setIsLoading(false);
    };

    image.onerror = (e) => {
      console.error("[CropCanvas] Image load error:", e);
      setLoadError("이미지를 불러올 수 없습니다");
      setIsLoading(false);
    };

    image.src = imageSrc;
  }, [imageSrc]);

  // Draw canvas when image or rect changes
  useEffect(() => {
    if (!canvasRef.current || !img || canvasSize.w === 0 || canvasSize.h === 0) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    // Clear and draw image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvasSize.w, canvasSize.h);

    // Draw selection overlay
    if (rect && rect.w > 5 && rect.h > 5) {
      // Darken non-selected areas
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      // Top
      ctx.fillRect(0, 0, canvasSize.w, rect.y);
      // Left
      ctx.fillRect(0, rect.y, rect.x, rect.h);
      // Right
      ctx.fillRect(rect.x + rect.w, rect.y, canvasSize.w - rect.x - rect.w, rect.h);
      // Bottom
      ctx.fillRect(0, rect.y + rect.h, canvasSize.w, canvasSize.h - rect.y - rect.h);

      // Draw selection border
      ctx.strokeStyle = "#3B82F6";
      ctx.lineWidth = 3;
      ctx.setLineDash([8, 4]);
      ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
      ctx.setLineDash([]);

      // Draw corner handles
      ctx.fillStyle = "#3B82F6";
      const handleSize = 12;
      [[0,0],[1,0],[0,1],[1,1]].forEach(([cx, cy]) => {
        const hx = rect.x + (cx ? rect.w - handleSize/2 : -handleSize/2);
        const hy = rect.y + (cy ? rect.h - handleSize/2 : -handleSize/2);
        ctx.fillRect(hx, hy, handleSize, handleSize);
      });

      // Draw size label
      const scale = img.naturalWidth / canvasSize.w;
      const actualW = Math.round(rect.w * scale);
      const actualH = Math.round(rect.h * scale);
      const labelText = `${actualW} × ${actualH}px`;
      ctx.font = "bold 14px sans-serif";
      const textWidth = ctx.measureText(labelText).width;
      const labelX = rect.x + rect.w / 2 - textWidth / 2 - 10;
      const labelY = rect.y + rect.h + 10;

      ctx.fillStyle = "#3B82F6";
      ctx.fillRect(labelX - 6, labelY, textWidth + 20, 26);
      ctx.fillStyle = "#fff";
      ctx.fillText(labelText, labelX + 4, labelY + 18);
    }
  }, [img, rect, canvasSize]);

  // Get mouse position relative to canvas
  const getPos = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const r = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    return {
      x: Math.max(0, Math.min(clientX - r.left, canvasSize.w)),
      y: Math.max(0, Math.min(clientY - r.top, canvasSize.h))
    };
  };

  const onMouseDown = (e) => {
    e.preventDefault();
    const pos = getPos(e);
    setStartPos(pos);
    setRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
    setDrawing(true);
  };

  const onMouseMove = (e) => {
    if (!drawing || !startPos) return;
    e.preventDefault();
    const pos = getPos(e);
    setRect({
      x: Math.min(startPos.x, pos.x),
      y: Math.min(startPos.y, pos.y),
      w: Math.abs(pos.x - startPos.x),
      h: Math.abs(pos.y - startPos.y),
    });
  };

  const onMouseUp = () => {
    setDrawing(false);
  };

  const confirmCrop = () => {
    if (!rect || rect.w < 20 || rect.h < 20 || !img) return;

    // Calculate scale factor
    const scale = img.naturalWidth / canvasSize.w;

    // Create crop canvas at original resolution
    const cropCanvas = document.createElement("canvas");
    const sw = Math.round(rect.w * scale);
    const sh = Math.round(rect.h * scale);
    cropCanvas.width = sw;
    cropCanvas.height = sh;

    const ctx = cropCanvas.getContext("2d");
    ctx.drawImage(
      img,
      Math.round(rect.x * scale),
      Math.round(rect.y * scale),
      sw,
      sh,
      0,
      0,
      sw,
      sh
    );

    const dataUrl = cropCanvas.toDataURL("image/png");
    onCropDone(dataUrl, pageIdx);
    setRect(null);
  };

  // No image source
  if (!imageSrc) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#94A3B8" }}>
        이미지를 선택해주세요
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: 60, textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 16 }}>⏳</div>
        <div style={{ color: "#64748B", fontSize: 14 }}>이미지 로딩 중...</div>
      </div>
    );
  }

  // Error state
  if (loadError) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "#EF4444" }}>
        <div style={{ fontSize: 32, marginBottom: 16 }}>❌</div>
        <div>{loadError}</div>
      </div>
    );
  }

  // Image not loaded yet
  if (!img || canvasSize.w === 0) {
    return (
      <div style={{ padding: 60, textAlign: "center" }}>
        <div style={{ fontSize: 32, marginBottom: 16 }}>⏳</div>
        <div style={{ color: "#64748B", fontSize: 14 }}>이미지 준비 중...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 12, padding: "12px 16px", background: "#f0f9ff", borderRadius: 8, border: "1px solid #bae6fd" }}>
        <span style={{fontSize: 14, color: "#0369a1", fontWeight: 600}}>
          💡 마우스로 드래그하여 크롭 영역을 선택하세요 (스크롤하여 전체 이미지 확인)
        </span>
      </div>

      {/* Scrollable container for large images */}
      <div
        ref={containerRef}
        style={{
          maxHeight: "70vh",
          maxWidth: "100%",
          overflow: "auto",
          borderRadius: 8,
          boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
          border: "2px solid #E2E8F0",
          background: "#F8FAFC"
        }}
      >
        <canvas
          ref={canvasRef}
          width={canvasSize.w}
          height={canvasSize.h}
          style={{
            display: "block",
            cursor: "crosshair",
          }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          onTouchStart={onMouseDown}
          onTouchMove={onMouseMove}
          onTouchEnd={onMouseUp}
        />
      </div>

      {/* Canvas size info */}
      <div style={{ marginTop: 8, fontSize: 12, color: "#94A3B8", textAlign: "center" }}>
        이미지 크기: {canvasSize.w} × {canvasSize.h}px
        {img && canvasSize.w < img.naturalWidth && (
          <span> (원본: {img.naturalWidth} × {img.naturalHeight}px)</span>
        )}
      </div>

      {rect && rect.w > 30 && rect.h > 30 && !drawing && (
        <div style={{ display: "flex", gap: 12, marginTop: 16, justifyContent: "center" }}>
          <button onClick={confirmCrop} style={{...btnBlueSm, padding: "12px 28px", fontSize: 15}}>
            ✓ 이 영역 크롭
          </button>
          <button onClick={() => setRect(null)} style={{...btnGraySm, padding: "12px 28px", fontSize: 15}}>
            다시 선택
          </button>
        </div>
      )}
    </div>
  );
}

// Export for use in other components
window.SharedCropComponents = {
  CropCanvas,
  loadImage,
  roundRect,
  fillRR,
  btnBlueSm,
  btnGraySm,
};
