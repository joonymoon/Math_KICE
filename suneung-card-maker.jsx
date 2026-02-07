import { useState, useRef, useCallback, useEffect } from "react";

/* ═══════════════════════════════════════════════
   Constants
   ═══════════════════════════════════════════════ */
const CARD_W = 720;

const THEMES = {
  blue: { name:"클래식 블루", g0:"#4A90D9", g1:"#2E6DB4", tagBg:"#EBF5FF", tagTx:"#3B7DD8" },
  dark: { name:"미드나이트", g0:"#1E293B", g1:"#0F172A", tagBg:"#334155", tagTx:"#CBD5E1" },
  warm: { name:"선셋 오렌지", g0:"#F59E0B", g1:"#EA580C", tagBg:"#FFF7ED", tagTx:"#C2410C" },
  mint: { name:"민트 오션", g0:"#06B6D4", g1:"#0891B2", tagBg:"#ECFEFF", tagTx:"#0E7490" },
  grape: { name:"그레이프", g0:"#8B5CF6", g1:"#6D28D9", tagBg:"#F5F3FF", tagTx:"#7C3AED" },
  forest: { name:"포레스트", g0:"#059669", g1:"#047857", tagBg:"#ECFDF5", tagTx:"#047857" },
};

const DIFFS = { "2점":"#16A34A", "3점":"#F59E0B", "4점":"#DC2626" };
const CATS = ["이차함수","삼각함수","수열","미분","적분","확률","통계","기하","지수로그","집합","함수","기타"];
const CAT_E = { 이차함수:"📈", 삼각함수:"📐", 수열:"🔢", 미분:"📉", 적분:"∫", 확률:"🎲", 통계:"📊", 기하:"📏", 지수로그:"🔬", 집합:"🔗", 함수:"ƒ", 기타:"📚" };
const EXAMS = ["수능","6월 모의평가","9월 모의평가","3월 학력평가","4월 학력평가","7월 학력평가","10월 학력평가"];

/* ═══════════════════════════════════════════════
   Canvas drawing helpers
   ═══════════════════════════════════════════════ */
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x+r,y);
  ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r);
  ctx.arcTo(x,y,x+w,y,r);
  ctx.closePath();
}

function fillRR(ctx, x, y, w, h, r, color) {
  roundRect(ctx, x, y, w, h, r);
  ctx.fillStyle = color;
  ctx.fill();
}

// Load image from data URL — no crossOrigin needed
function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Image load failed"));
    img.src = src;
  });
}

function drawTag(ctx, x, y, text, fontSize, bg, fg) {
  ctx.font = `500 ${fontSize}px sans-serif`;
  const tw = ctx.measureText(text).width;
  const pw = tw + 22;
  const ph = 26;
  fillRR(ctx, x, y, pw, ph, ph/2, bg);
  ctx.fillStyle = fg;
  ctx.fillText(text, x + 11, y + 17);
  return pw;
}

/* ─── Generate card PNG via Canvas ─── */
async function generateCardPNG(imgDataUrl, meta, themeKey) {
  const T = THEMES[themeKey];
  const diffColor = DIFFS[meta.difficulty] || "#F59E0B";
  const emoji = CAT_E[meta.category] || "📚";

  // Use system font stack — avoids font loading issues entirely
  const fontFamily = '-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
  const fontBold = (size) => `bold ${size}px ${fontFamily}`;
  const fontMed = (size) => `500 ${size}px ${fontFamily}`;
  const fontNorm = (size) => `${size}px ${fontFamily}`;

  // Load problem image
  const problemImg = await loadImage(imgDataUrl);

  const PAD = 24;
  const innerW = CARD_W - PAD * 2;
  const imgScale = innerW / problemImg.width;
  const imgH = Math.round(problemImg.height * imgScale);

  // Calculate section heights
  const headerH = 82;
  const imgPadding = 20;
  const imgSectionH = imgPadding + imgH + imgPadding;
  const tagSectionH = 56;
  const hintSectionH = 50;
  const sourceSectionH = 40;
  const totalH = headerH + imgSectionH + 1 + tagSectionH + hintSectionH + sourceSectionH;

  // Create canvas
  const canvas = document.createElement("canvas");
  canvas.width = CARD_W;
  canvas.height = Math.ceil(totalH);
  const ctx = canvas.getContext("2d");

  // White background with rounded clip
  ctx.save();
  roundRect(ctx, 0, 0, CARD_W, totalH, 20);
  ctx.clip();
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, CARD_W, totalH);

  let y = 0;

  // ── 1. Header ──
  const grad = ctx.createLinearGradient(0, 0, CARD_W, headerH);
  grad.addColorStop(0, T.g0);
  grad.addColorStop(1, T.g1);
  ctx.fillStyle = grad;
  ctx.fillRect(0, y, CARD_W, headerH);

  // Title
  ctx.fillStyle = "#FFFFFF";
  ctx.font = fontBold(18);
  ctx.fillText(`${emoji}  오늘의 수학 문제`, PAD, y + 34);

  // Difficulty badge
  ctx.font = fontBold(12);
  const badgeText = meta.difficulty;
  const badgeW = ctx.measureText(badgeText).width + 22;
  const badgeX = CARD_W - PAD - badgeW;
  fillRR(ctx, badgeX, y + 18, badgeW, 24, 12, diffColor);
  ctx.fillStyle = "#FFFFFF";
  ctx.font = fontBold(12);
  ctx.fillText(badgeText, badgeX + 11, y + 34);

  // Subtitle
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  ctx.font = fontNorm(13);
  ctx.fillText(`${meta.year}학년도 ${meta.examName}  ·  ${meta.number}번`, PAD, y + 62);
  y += headerH;

  // ── 2. Problem image section ──
  ctx.fillStyle = "#FAFBFC";
  ctx.fillRect(0, y, CARD_W, imgSectionH);

  const imgX = PAD;
  const imgY = y + imgPadding;

  // White background behind image
  fillRR(ctx, imgX, imgY, innerW, imgH, 12, "#FFFFFF");

  // Draw the problem image clipped with rounded corners
  ctx.save();
  roundRect(ctx, imgX, imgY, innerW, imgH, 12);
  ctx.clip();
  ctx.drawImage(problemImg, imgX, imgY, innerW, imgH);
  ctx.restore();

  // Image border
  ctx.strokeStyle = "#E2E8F0";
  ctx.lineWidth = 1;
  roundRect(ctx, imgX, imgY, innerW, imgH, 12);
  ctx.stroke();
  y += imgSectionH;

  // ── 3. Divider ──
  ctx.fillStyle = "#F1F5F9";
  ctx.fillRect(0, y, CARD_W, 1);
  y += 1;

  // ── 4. Tags ──
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, y, CARD_W, tagSectionH);
  let tagX = PAD;
  const tagY = y + 15;
  const tagTexts = [`#${meta.category}`, `#${meta.difficulty}`, `#${meta.year}${meta.examName}`];
  for (const t of tagTexts) {
    const w = drawTag(ctx, tagX, tagY, t, 12, T.tagBg, T.tagTx);
    tagX += w + 8;
  }
  y += tagSectionH;

  // ── 5. Hint ──
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, y, CARD_W, hintSectionH);
  fillRR(ctx, PAD, y + 10, CARD_W - PAD*2, 30, 8, "#F8FAFC");
  ctx.fillStyle = "#94A3B8";
  ctx.font = fontNorm(12);
  ctx.fillText('💡 힌트가 필요하면 "힌트"를 입력하세요', PAD + 12, y + 30);
  y += hintSectionH;

  // ── 6. Source ──
  ctx.fillStyle = "#F8FAFC";
  ctx.fillRect(0, y, CARD_W, sourceSectionH);
  ctx.fillStyle = "#A0AEC0";
  ctx.font = fontNorm(11);
  const srcText = `${meta.year}학년도 ${meta.examName} 수학 ${meta.number}번  ·  한국교육과정평가원`;
  const srcW = ctx.measureText(srcText).width;
  ctx.fillText(srcText, (CARD_W - srcW) / 2, y + 24);

  ctx.restore();

  // Outer border
  ctx.strokeStyle = "rgba(0,0,0,0.06)";
  ctx.lineWidth = 1;
  roundRect(ctx, 0.5, 0.5, CARD_W - 1, totalH - 1, 20);
  ctx.stroke();

  // Convert to blob for reliable download
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      resolve(blob);
    }, "image/png");
  });
}

/* ═══════════════════════════════════════════════
   PDF.js Loader
   ═══════════════════════════════════════════════ */
function usePdfLoader() {
  const [ready, setReady] = useState(false);
  const libRef = useRef(null);

  useEffect(() => {
    if (window.pdfjsLib) {
      libRef.current = window.pdfjsLib;
      setReady(true);
      return;
    }
    const s = document.createElement("script");
    s.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
    s.onload = () => {
      const lib = window.pdfjsLib;
      if (lib) {
        lib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        libRef.current = lib;
        setReady(true);
      }
    };
    document.head.appendChild(s);
  }, []);

  const renderPDF = useCallback(async (file) => {
    const lib = libRef.current;
    if (!lib) throw new Error("PDF.js not loaded");
    const buf = await file.arrayBuffer();
    const pdf = await lib.getDocument({ data: buf }).promise;
    const results = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const vp = page.getViewport({ scale: 2 });
      const c = document.createElement("canvas");
      c.width = vp.width;
      c.height = vp.height;
      await page.render({ canvasContext: c.getContext("2d"), viewport: vp }).promise;
      results.push({ src: c.toDataURL("image/png"), name: `페이지 ${i}` });
    }
    return results;
  }, []);

  return { pdfReady: ready, renderPDF };
}

/* ═══════════════════════════════════════════════
   Crop Canvas
   ═══════════════════════════════════════════════ */
function CropCanvas({ imageSrc, pageIdx, onCropDone }) {
  const imgRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [start, setStart] = useState(null);
  const [rect, setRect] = useState(null);
  const [scale, setScale] = useState(1);

  useEffect(() => { setRect(null); }, [imageSrc]);

  const getPos = (e) => {
    const r = imgRef.current.getBoundingClientRect();
    const cx = e.touches ? e.touches[0].clientX : e.clientX;
    const cy = e.touches ? e.touches[0].clientY : e.clientY;
    return { x: cx - r.left, y: cy - r.top };
  };

  const onDown = (e) => {
    e.preventDefault();
    const p = getPos(e);
    setStart(p);
    setRect({ x: p.x, y: p.y, w: 0, h: 0 });
    setDrawing(true);
  };

  const onMove = (e) => {
    if (!drawing || !start) return;
    e.preventDefault();
    const p = getPos(e);
    setRect({
      x: Math.min(start.x, p.x),
      y: Math.min(start.y, p.y),
      w: Math.abs(p.x - start.x),
      h: Math.abs(p.y - start.y),
    });
  };

  const onUp = () => setDrawing(false);

  const confirmCrop = () => {
    if (!rect || rect.w < 10 || rect.h < 10) return;
    const c = document.createElement("canvas");
    const sw = Math.round(rect.w * scale);
    const sh = Math.round(rect.h * scale);
    c.width = sw;
    c.height = sh;
    const ctx = c.getContext("2d");

    const tmp = new Image();
    tmp.onload = () => {
      ctx.drawImage(
        tmp,
        Math.round(rect.x * scale),
        Math.round(rect.y * scale),
        sw, sh,
        0, 0, sw, sh
      );
      const dataUrl = c.toDataURL("image/png");
      onCropDone(dataUrl, pageIdx);
      setRect(null);
    };
    tmp.src = imageSrc;
  };

  if (!imageSrc) return null;

  return (
    <div>
      <div style={{ position: "relative", display: "inline-block", maxWidth: "100%", lineHeight: 0 }}>
        <img
          ref={imgRef}
          src={imageSrc}
          alt=""
          draggable={false}
          style={{ maxWidth: "100%", maxHeight: 550, display: "block", borderRadius: 8, userSelect: "none" }}
          onLoad={() => {
            const el = imgRef.current;
            if (el) setScale(el.naturalWidth / el.clientWidth);
          }}
        />
        <div
          style={{ position: "absolute", inset: 0, cursor: "crosshair" }}
          onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} onMouseLeave={onUp}
          onTouchStart={onDown} onTouchMove={onMove} onTouchEnd={onUp}
        >
          {rect && rect.w > 3 && rect.h > 3 && (
            <>
              <div style={{ position:"absolute", background:"rgba(0,0,0,.4)", pointerEvents:"none", top:0, left:0, width:"100%", height:rect.y }} />
              <div style={{ position:"absolute", background:"rgba(0,0,0,.4)", pointerEvents:"none", top:rect.y, left:0, width:rect.x, height:rect.h }} />
              <div style={{ position:"absolute", background:"rgba(0,0,0,.4)", pointerEvents:"none", top:rect.y, left:rect.x+rect.w, right:0, height:rect.h }} />
              <div style={{ position:"absolute", background:"rgba(0,0,0,.4)", pointerEvents:"none", top:rect.y+rect.h, left:0, width:"100%", bottom:0 }} />
              <div style={{
                position:"absolute", left:rect.x, top:rect.y, width:rect.w, height:rect.h,
                border:"2.5px dashed #3B82F6", borderRadius:3, pointerEvents:"none"
              }}>
                {[[0,0],[1,0],[0,1],[1,1]].map(([cx,cy],i) => (
                  <div key={i} style={{
                    position:"absolute", width:8, height:8, borderRadius:2, background:"#3B82F6",
                    left: cx ? "calc(100% - 4px)" : -4,
                    top: cy ? "calc(100% - 4px)" : -4,
                  }} />
                ))}
              </div>
              <div style={{
                position:"absolute",
                left: rect.x + rect.w/2 - 32,
                top: rect.y + rect.h + 6,
                background:"#3B82F6", color:"#fff", fontSize:10,
                padding:"2px 8px", borderRadius:4, pointerEvents:"none", whiteSpace:"nowrap"
              }}>
                {Math.round(rect.w*scale)} × {Math.round(rect.h*scale)}
              </div>
            </>
          )}
        </div>
      </div>

      {rect && rect.w > 20 && rect.h > 20 && !drawing && (
        <div style={{ display:"flex", gap:8, marginTop:12 }}>
          <button onClick={confirmCrop} style={btnBlueSm}>✓ 이 영역 크롭</button>
          <button onClick={() => setRect(null)} style={btnGraySm}>다시 선택</button>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Main App
   ═══════════════════════════════════════════════ */
export default function App() {
  // Load Noto Sans KR (for display only, canvas uses system fonts)
  useEffect(() => {
    if (!document.querySelector('link[href*="Noto+Sans+KR"]')) {
      const l = document.createElement("link");
      l.href = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap";
      l.rel = "stylesheet";
      document.head.appendChild(l);
    }
  }, []);

  const { pdfReady, renderPDF } = usePdfLoader();

  const [step, setStep] = useState(0); // 0 upload, 1 crop, 2 card
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [crops, setCrops] = useState([]);
  const [merged, setMerged] = useState(null);
  const [activePg, setActivePg] = useState(0);
  const [meta, setMeta] = useState({
    number: 1, year: 2025, examName: "수능",
    difficulty: "3점", category: "미분", theme: "blue",
  });
  const [cardBlob, setCardBlob] = useState(null);
  const [cardPreview, setCardPreview] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  // ─── Handle file uploads ───
  const handleFiles = async (files) => {
    setError(null);
    for (const f of files) {
      if (f.type === "application/pdf") {
        if (!pdfReady) { setError("PDF.js 로딩 중... 잠시 후 다시 시도하세요."); return; }
        setLoading(true);
        try {
          const p = await renderPDF(f);
          setPages(prev => [...prev, ...p]);
        } catch (e) {
          setError("PDF 변환 실패: " + e.message);
        }
        setLoading(false);
      } else if (f.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (ev) => setPages(prev => [...prev, { src: ev.target.result, name: f.name }]);
        reader.readAsDataURL(f);
      }
    }
  };

  // ─── Auto-merge crops ───
  useEffect(() => {
    if (crops.length === 0) { setMerged(null); return; }
    if (crops.length === 1) { setMerged(crops[0].dataUrl); return; }

    const loadAll = crops.map(c => loadImage(c.dataUrl));
    Promise.all(loadAll).then(loaded => {
      const maxW = Math.max(...loaded.map(i => i.width));
      const gap = 16;
      const totalH = loaded.reduce((s, i) => s + i.height, 0) + gap * (loaded.length - 1);
      const c = document.createElement("canvas");
      c.width = maxW;
      c.height = totalH;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, c.width, c.height);
      let yy = 0;
      loaded.forEach(im => {
        ctx.drawImage(im, Math.round((maxW - im.width) / 2), yy);
        yy += im.height + gap;
      });
      setMerged(c.toDataURL("image/png"));
    });
  }, [crops]);

  // ─── Generate card when settings change ───
  useEffect(() => {
    if (step !== 2 || !merged) return;

    let cancelled = false;
    setGenerating(true);
    setError(null);

    generateCardPNG(merged, meta, meta.theme)
      .then(blob => {
        if (cancelled) return;
        setCardBlob(blob);
        // Create preview URL
        const url = URL.createObjectURL(blob);
        setCardPreview(prev => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
        setGenerating(false);
      })
      .catch(err => {
        if (cancelled) return;
        setError("카드 생성 실패: " + err.message);
        setGenerating(false);
      });

    return () => { cancelled = true; };
  }, [step, merged, meta.number, meta.year, meta.examName, meta.difficulty, meta.category, meta.theme]);

  // ─── Download as PNG (via Blob) ───
  const downloadPNG = () => {
    if (!cardBlob) return;
    const url = URL.createObjectURL(cardBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `수능_${meta.year}_${meta.number}번_카드.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const T = THEMES[meta.theme];
  const stepLabels = ["PDF 업로드", "문제 크롭", "카드 생성"];

  return (
    <div style={{ fontFamily:'"Noto Sans KR",-apple-system,sans-serif', background:"#F1F5F9", minHeight:"100vh" }}>

      {/* ─── Top Bar ─── */}
      <div style={{ background:"linear-gradient(135deg,#1E293B,#0F172A)", padding:"18px 24px", color:"#fff" }}>
        <div style={{ maxWidth:1060, margin:"0 auto", display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:38, height:38, borderRadius:10, background:"rgba(255,255,255,.08)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>✂️</div>
          <div>
            <div style={{ fontSize:16, fontWeight:700 }}>수능 문제 카드 메이커</div>
            <div style={{ fontSize:11, opacity:.5 }}>PDF 업로드 → 크롭 → 카카오톡 발송용 PNG</div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth:1060, margin:"0 auto", padding:"16px 16px 60px" }}>

        {/* Step tabs */}
        <div style={{ display:"flex", gap:4, marginBottom:20 }}>
          {stepLabels.map((s,i) => (
            <button key={i}
              onClick={() => { if (i===0 || (i===1 && pages.length) || (i===2 && merged)) setStep(i); }}
              style={{
                flex:1, padding:"10px 0", borderRadius:10, border:"none", cursor:"pointer",
                fontSize:13, fontWeight: i===step ? 700 : 500, transition:"all .2s",
                background: i===step ? "#1E293B" : i<step ? "#94A3B8" : "#E2E8F0",
                color: i<=step ? "#fff" : "#94A3B8"
              }}>
              {i<step ? "✓ " : `${i+1}. `}{s}
            </button>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div style={{ background:"#FEF2F2", border:"1px solid #FECACA", borderRadius:12, padding:"12px 16px", marginBottom:16, color:"#DC2626", fontSize:13, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} style={{ background:"none", border:"none", cursor:"pointer", color:"#DC2626", fontWeight:700 }}>✕</button>
          </div>
        )}

        {/* ═══ Step 0: Upload ═══ */}
        {step === 0 && (
          <div style={cardStyle}>
            <h2 style={h2Style}>📄 PDF 또는 이미지 업로드</h2>
            <p style={descStyle}>
              수능 시험지 PDF를 올리면 자동으로 페이지별 이미지로 변환됩니다.
              {!pdfReady && <span style={{ color:"#F59E0B", display:"block", marginTop:4 }}>⏳ PDF.js 로딩 중...</span>}
            </p>

            <div
              onClick={() => inputRef.current?.click()}
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); handleFiles(Array.from(e.dataTransfer.files)); }}
              style={{ border:"2px dashed #CBD5E1", borderRadius:16, padding: loading ? "36px 20px" : "44px 20px",
                textAlign:"center", cursor:"pointer", background:"#F8FAFC", transition:"all .2s" }}
              onMouseEnter={e => e.currentTarget.style.borderColor="#3B82F6"}
              onMouseLeave={e => e.currentTarget.style.borderColor="#CBD5E1"}
            >
              {loading ? (
                <>
                  <div style={{ fontSize:32, marginBottom:6, animation:"spin 1s linear infinite" }}>⏳</div>
                  <div style={{ fontSize:14, fontWeight:600, color:"#1E293B" }}>PDF 변환 중...</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize:40, marginBottom:8 }}>📁</div>
                  <div style={{ fontSize:15, fontWeight:600, color:"#1E293B" }}>클릭 또는 드래그로 파일 추가</div>
                  <div style={{ fontSize:12, color:"#94A3B8", marginTop:4 }}>PDF, PNG, JPG · 여러 파일 가능</div>
                </>
              )}
            </div>
            <input ref={inputRef} type="file" accept=".pdf,image/*" multiple
              onChange={e => { handleFiles(Array.from(e.target.files)); e.target.value = ""; }}
              style={{ display:"none" }} />

            {pages.length > 0 && (
              <>
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(120px, 1fr))", gap:10, marginTop:20 }}>
                  {pages.map((p,i) => (
                    <div key={i} style={{ borderRadius:10, overflow:"hidden", border:"1px solid #E2E8F0", background:"#fff" }}>
                      <img src={p.src} alt="" style={{ width:"100%", height:120, objectFit:"cover", display:"block" }} />
                      <div style={{ padding:"5px 8px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                        <span style={{ fontSize:10, fontWeight:600, color:"#475569" }}>{p.name}</span>
                        <button onClick={() => setPages(prev => prev.filter((_,j)=>j!==i))}
                          style={{ background:"none", border:"none", cursor:"pointer", color:"#EF4444", fontSize:12, fontWeight:700 }}>✕</button>
                      </div>
                    </div>
                  ))}
                </div>
                <button onClick={() => { setStep(1); setActivePg(0); }} style={{ ...btnDark, marginTop:20 }}>
                  문제 크롭하기 →
                </button>
              </>
            )}
          </div>
        )}

        {/* ═══ Step 1: Crop ═══ */}
        {step === 1 && (
          <div style={cardStyle}>
            <h2 style={h2Style}>✂️ 문제 영역 선택</h2>
            <p style={descStyle}>
              드래그로 문제 영역을 선택하세요. <b>2페이지 문제</b>는 각 페이지에서 크롭 → 자동 세로 병합.
            </p>

            {/* Page tabs */}
            <div style={{ display:"flex", gap:6, marginBottom:14, flexWrap:"wrap" }}>
              {pages.map((p,i) => (
                <button key={i} onClick={() => setActivePg(i)}
                  style={{ padding:"6px 14px", borderRadius:8, border:"none", cursor:"pointer", fontSize:12, fontWeight:600,
                    background: activePg===i ? "#1E293B" : "#F1F5F9", color: activePg===i ? "#fff" : "#64748B" }}>
                  📄 {p.name}
                </button>
              ))}
            </div>

            <div style={{ background:"#F8FAFC", borderRadius:12, padding:14, border:"1px solid #E2E8F0" }}>
              <CropCanvas
                imageSrc={pages[activePg]?.src}
                pageIdx={activePg}
                onCropDone={(dataUrl, pgIdx) => setCrops(prev => [...prev, { dataUrl, pgIdx }])}
              />
            </div>

            {crops.length > 0 && (
              <div style={{ marginTop:20 }}>
                <div style={{ fontSize:14, fontWeight:700, color:"#1E293B", marginBottom:10, display:"flex", alignItems:"center", gap:8 }}>
                  🧩 크롭 ({crops.length}개)
                  {crops.length >= 2 && <span style={{ background:"#DCFCE7", color:"#166534", fontSize:11, padding:"2px 10px", borderRadius:10, fontWeight:600 }}>자동 병합</span>}
                </div>
                <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
                  {crops.map((c,i) => (
                    <div key={i} style={{ border:"1px solid #E2E8F0", borderRadius:10, overflow:"hidden", width:140, background:"#fff" }}>
                      <img src={c.dataUrl} alt="" style={{ width:"100%", height:100, objectFit:"contain", background:"#F8FAFC", display:"block" }} />
                      <div style={{ padding:"4px 8px", display:"flex", justifyContent:"space-between", fontSize:10, color:"#64748B" }}>
                        <span>페이지 {c.pgIdx+1}</span>
                        <button onClick={() => { setCrops(prev => prev.filter((_,j)=>j!==i)); setMerged(null); }}
                          style={{ background:"none", border:"none", cursor:"pointer", color:"#EF4444", fontSize:10, fontWeight:700 }}>삭제</button>
                      </div>
                    </div>
                  ))}
                </div>

                {merged && (
                  <div style={{ marginTop:14, background:"#F8FAFC", borderRadius:12, padding:14, border:"1px solid #E2E8F0" }}>
                    <div style={{ fontSize:13, fontWeight:600, color:"#475569", marginBottom:8 }}>📋 최종 문제 이미지</div>
                    <img src={merged} alt="" style={{ maxWidth:"100%", maxHeight:320, objectFit:"contain", borderRadius:8, display:"block" }} />
                  </div>
                )}
              </div>
            )}

            <div style={{ display:"flex", gap:10, marginTop:20 }}>
              <button onClick={() => setStep(0)} style={btnGray}>← 뒤로</button>
              {merged && <button onClick={() => setStep(2)} style={btnDark}>카드 생성 →</button>}
            </div>
          </div>
        )}

        {/* ═══ Step 2: Card ═══ */}
        {step === 2 && (
          <div style={{ display:"flex", gap:20, flexWrap:"wrap", alignItems:"flex-start" }}>

            {/* Left: Settings */}
            <div style={{ ...cardStyle, flex:1, minWidth:280 }}>
              <h2 style={{ ...h2Style, marginBottom:18 }}>⚙️ 문제 정보</h2>

              <div style={{ display:"flex", gap:12, marginBottom:14 }}>
                <FieldWrap label="문제 번호">
                  <input type="number" min={1} max={30} value={meta.number}
                    onChange={e => setMeta(p => ({...p, number:+e.target.value}))} style={inputStyle} />
                </FieldWrap>
                <FieldWrap label="연도">
                  <input type="number" min={2010} max={2030} value={meta.year}
                    onChange={e => setMeta(p => ({...p, year:+e.target.value}))} style={inputStyle} />
                </FieldWrap>
              </div>

              <FieldWrap label="시험명">
                <select value={meta.examName} onChange={e => setMeta(p => ({...p, examName:e.target.value}))} style={inputStyle}>
                  {EXAMS.map(ex => <option key={ex}>{ex}</option>)}
                </select>
              </FieldWrap>

              <FieldWrap label="배점">
                <div style={{ display:"flex", gap:6 }}>
                  {["2점","3점","4점"].map(d => (
                    <button key={d} onClick={() => setMeta(p => ({...p, difficulty:d}))}
                      style={{ padding:"6px 16px", borderRadius:20, border:"none", cursor:"pointer", fontSize:13, fontWeight:700,
                        background: meta.difficulty===d ? DIFFS[d] : "#F1F5F9",
                        color: meta.difficulty===d ? "#fff" : "#64748B", transition:"all .15s" }}>{d}</button>
                  ))}
                </div>
              </FieldWrap>

              <FieldWrap label="카테고리">
                <div style={{ display:"flex", gap:5, flexWrap:"wrap" }}>
                  {CATS.map(c => (
                    <button key={c} onClick={() => setMeta(p => ({...p, category:c}))}
                      style={{ padding:"5px 11px", borderRadius:14, border:"none", cursor:"pointer", fontSize:11,
                        fontWeight: meta.category===c ? 700 : 500,
                        background: meta.category===c ? T.g0 : "#F1F5F9",
                        color: meta.category===c ? "#fff" : "#64748B", transition:"all .15s" }}>
                      {CAT_E[c]} {c}
                    </button>
                  ))}
                </div>
              </FieldWrap>

              <FieldWrap label="테마">
                <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                  {Object.entries(THEMES).map(([k,t]) => (
                    <button key={k} onClick={() => setMeta(p => ({...p, theme:k}))} title={t.name}
                      style={{ width:40, height:40, borderRadius:10, border:"none", cursor:"pointer",
                        background:`linear-gradient(135deg,${t.g0},${t.g1})`,
                        outline: meta.theme===k ? "3px solid #1E293B" : "none",
                        outlineOffset:3, transition:"all .15s" }} />
                  ))}
                </div>
              </FieldWrap>

              {/* Download button */}
              <button
                onClick={downloadPNG}
                disabled={!cardBlob || generating}
                style={{
                  width:"100%", marginTop:24, padding:"16px 0", borderRadius:12, border:"none",
                  fontSize:16, fontWeight:700, cursor: cardBlob && !generating ? "pointer" : "default",
                  background: cardBlob && !generating
                    ? "linear-gradient(135deg,#2563EB,#1D4ED8)"
                    : "#CBD5E1",
                  color:"#fff", transition:"all .2s",
                  boxShadow: cardBlob && !generating ? "0 4px 14px rgba(37,99,235,.3)" : "none",
                }}
              >
                {generating ? "⏳ 카드 생성 중..." : "📲  PNG 다운로드"}
              </button>

              {cardBlob && !generating && (
                <div style={{ fontSize:11, color:"#16A34A", textAlign:"center", marginTop:8, fontWeight:600 }}>
                  ✓ 카드 생성 완료 — 720px PNG · 카카오톡 바로 전송 가능
                </div>
              )}

              <button onClick={() => setStep(1)}
                style={{ ...btnGray, width:"100%", marginTop:12, textAlign:"center" }}>← 크롭 수정</button>
            </div>

            {/* Right: KakaoTalk Preview */}
            <div style={{ width:370, flexShrink:0 }}>
              <div style={{ fontSize:13, fontWeight:700, color:"#64748B", marginBottom:10 }}>📱 카카오톡 미리보기</div>

              <div style={{ background:"#9BBBD4", borderRadius:20, overflow:"hidden", boxShadow:"0 4px 24px rgba(0,0,0,.15)" }}>
                {/* Top bar */}
                <div style={{ background:"#3C1E1E", color:"#fff", padding:"10px 16px", display:"flex", justifyContent:"space-between", fontSize:14 }}>
                  <span style={{ opacity:.6 }}>‹</span>
                  <span style={{ fontWeight:700, fontSize:14 }}>수학봇</span>
                  <span style={{ opacity:.6 }}>≡</span>
                </div>

                {/* Chat */}
                <div style={{ padding:14 }}>
                  <div style={{ display:"flex", gap:8, alignItems:"flex-start" }}>
                    <div style={{ width:34, height:34, borderRadius:10, background:"#FFE066", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16, flexShrink:0 }}>🤖</div>
                    <div style={{ maxWidth:290 }}>
                      <div style={{ fontSize:10, color:"#5C4033", marginBottom:3, fontWeight:500 }}>수학봇</div>
                      {cardPreview ? (
                        <img src={cardPreview} alt="card" style={{ width:"100%", borderRadius:12, display:"block", boxShadow:"0 1px 4px rgba(0,0,0,.08)" }} />
                      ) : (
                        <div style={{ background:"#fff", borderRadius:12, padding:32, textAlign:"center" }}>
                          <div style={{ fontSize:20 }}>⏳</div>
                          <div style={{ fontSize:11, color:"#94A3B8", marginTop:6 }}>카드 생성 중...</div>
                        </div>
                      )}
                      <div style={{ fontSize:9, color:"#6B5B4E", marginTop:3, textAlign:"right" }}>
                        {new Date().getHours()}:{String(new Date().getMinutes()).padStart(2,"0")}
                      </div>
                    </div>
                  </div>

                  {/* Quick replies */}
                  <div style={{ display:"flex", gap:5, justifyContent:"center", marginTop:12, flexWrap:"wrap" }}>
                    {["①","②","③","④","⑤"].map(n => (
                      <span key={n} style={{ background:"#fff", border:"1px solid #D6C9BC", borderRadius:14, padding:"4px 12px", fontSize:12, fontWeight:600, color:"#4A3728" }}>{n}</span>
                    ))}
                  </div>
                </div>

                {/* Input bar */}
                <div style={{ background:"#fff", padding:"8px 14px", display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ flex:1, background:"#F1F5F9", borderRadius:18, padding:"7px 14px", fontSize:12, color:"#94A3B8" }}>메시지 입력...</div>
                  <div style={{ width:28, height:28, borderRadius:"50%", background:"#FFE066", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12 }}>➤</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Shared ─── */
function FieldWrap({ label, children }) {
  return (
    <div style={{ marginBottom:14, flex:1 }}>
      <label style={{ display:"block", fontSize:11, fontWeight:700, color:"#64748B", marginBottom:5, letterSpacing:.3 }}>{label}</label>
      {children}
    </div>
  );
}

const cardStyle = { background:"#fff", borderRadius:16, padding:24, boxShadow:"0 1px 3px rgba(0,0,0,.04)" };
const h2Style = { fontSize:17, fontWeight:700, color:"#1E293B", margin:"0 0 6px" };
const descStyle = { fontSize:13, color:"#64748B", margin:"0 0 16px", lineHeight:1.6 };
const inputStyle = { width:"100%", padding:"8px 12px", borderRadius:8, border:"1px solid #E2E8F0", fontSize:14, outline:"none", fontFamily:"inherit", background:"#fff" };
const btnDark = { background:"#1E293B", color:"#fff", border:"none", borderRadius:10, padding:"11px 24px", fontSize:14, fontWeight:700, cursor:"pointer" };
const btnGray = { background:"#F1F5F9", color:"#475569", border:"none", borderRadius:10, padding:"11px 24px", fontSize:14, fontWeight:600, cursor:"pointer" };
const btnBlueSm = { background:"#3B82F6", color:"#fff", border:"none", borderRadius:8, padding:"8px 16px", fontSize:13, fontWeight:700, cursor:"pointer" };
const btnGraySm = { background:"#F1F5F9", color:"#64748B", border:"none", borderRadius:8, padding:"8px 16px", fontSize:13, fontWeight:600, cursor:"pointer" };
