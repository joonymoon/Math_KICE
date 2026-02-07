/**
 * Crop Modal Component
 * Admin 페이지에서 사용하는 이미지 크롭 모달
 */

const { useState, useEffect, useRef } = React;
const { CropCanvas, loadImage } = window.SharedCropComponents;

/* ═══════════════════════════════════════════════
   Main Crop Modal Component
   ═══════════════════════════════════════════════ */

function CropModal({ problemId, existingImageUrl, onClose, onSuccess }) {
  const [problemData, setProblemData] = useState(null);
  const [imageSrc, setImageSrc] = useState(null);  // Start with no image - always use PDF
  const [croppedImage, setCroppedImage] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("idle"); // idle, uploading, success, error
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);

  // PDF page navigation state
  const [pdfDoc, setPdfDoc] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoadingPage, setIsLoadingPage] = useState(false);

  // Thumbnail view for PDF pages
  const [showThumbnails, setShowThumbnails] = useState(false);
  const [thumbnails, setThumbnails] = useState([]);  // Array of data URLs
  const [isLoadingThumbnails, setIsLoadingThumbnails] = useState(false);

  // Metadata form fields
  const [metadata, setMetadata] = useState({
    subject: "수1",  // 수1, 수2
    difficulty: "3점",  // 2점, 3점, 4점
    answer: "",
    unit: "미분",
    solution: ""
  });

  // Load problem metadata on mount (but NOT the image)
  useEffect(() => {
    async function loadMetadata() {
      try {
        const response = await fetch(`/problem/${problemId}/metadata`, {
          credentials: "include",
        });
        if (!response.ok) throw new Error("Failed to load metadata");
        const data = await response.json();
        setProblemData(data);

        // Map English subject back to Korean for UI
        const subjectReverseMap = {
          "Math1": "수1",
          "Math2": "수2"
        };

        // Set metadata from problem data
        setMetadata({
          subject: subjectReverseMap[data.subject] || "수1",
          difficulty: data.difficulty || "3점",
          answer: data.answer || "",
          unit: data.category || "미분",
          solution: data.solution || ""
        });

        // DO NOT load existing image - always require PDF upload for accuracy
      } catch (error) {
        console.error("Error loading metadata:", error);
        setErrorMessage("문제 정보를 불러올 수 없습니다");
      }
    }
    loadMetadata();
  }, [problemId]);

  // Handle file upload
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if it's an image or PDF
    const isImage = file.type.startsWith("image/");
    const isPDF = file.type === "application/pdf";

    if (!isImage && !isPDF) {
      setErrorMessage("이미지 또는 PDF 파일만 업로드 가능합니다");
      return;
    }

    if (isPDF) {
      await handlePDFUpload(file);
    } else {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImageSrc(event.target.result);
        setCroppedImage(null); // Reset crop
        setErrorMessage("");
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle PDF file upload and convert to image
  const handlePDFUpload = async (file) => {
    try {
      // Check if PDF.js is loaded
      if (!window.pdfjsLib) {
        setErrorMessage("PDF 라이브러리를 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
        return;
      }

      setErrorMessage("PDF 로딩 중...");

      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = window.pdfjsLib.getDocument({ data: arrayBuffer });
      const pdf = await loadingTask.promise;

      // Store PDF document for page navigation
      setPdfDoc(pdf);
      setTotalPages(pdf.numPages);
      setCurrentPage(1);
      setIsLoadingPage(true);  // Set loading state synchronously BEFORE rendering

      // Render first page
      await renderPdfPage(pdf, 1);
      setErrorMessage("");
    } catch (error) {
      console.error("PDF conversion error:", error);
      setErrorMessage("PDF 변환 실패: " + (error.message || "알 수 없는 오류"));
    }
  };

  // Render specific PDF page
  // NOTE: isLoadingPage should be set TRUE by caller BEFORE calling this function
  const renderPdfPage = async (pdf, pageNum) => {
    try {
      const page = await pdf.getPage(pageNum);

      const viewport = page.getViewport({ scale: 2.0 }); // Higher quality
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise;

      const dataUrl = canvas.toDataURL("image/png");
      setImageSrc(dataUrl);
      setCroppedImage(null);
      setIsLoadingPage(false);
    } catch (error) {
      console.error("Page render error:", error);
      setErrorMessage("페이지 렌더링 실패: " + (error.message || "알 수 없는 오류"));
      setIsLoadingPage(false);
    }
  };

  // Navigate to previous page
  const goToPrevPage = async () => {
    if (currentPage > 1 && pdfDoc && !isLoadingPage) {
      const newPage = currentPage - 1;
      setIsLoadingPage(true);  // Set SYNCHRONOUSLY before any async work
      setCurrentPage(newPage);
      await renderPdfPage(pdfDoc, newPage);
    }
  };

  // Navigate to next page
  const goToNextPage = async () => {
    if (currentPage < totalPages && pdfDoc && !isLoadingPage) {
      const newPage = currentPage + 1;
      setIsLoadingPage(true);  // Set SYNCHRONOUSLY before any async work
      setCurrentPage(newPage);
      await renderPdfPage(pdfDoc, newPage);
    }
  };

  // Jump to specific page
  const goToPage = async (pageNum) => {
    if (pageNum >= 1 && pageNum <= totalPages && pdfDoc && !isLoadingPage) {
      setIsLoadingPage(true);  // Set SYNCHRONOUSLY before any async work
      setCurrentPage(pageNum);
      await renderPdfPage(pdfDoc, pageNum);
    }
  };

  // Generate thumbnails for all pages
  const generateThumbnails = async () => {
    if (!pdfDoc || isLoadingThumbnails) return;

    setIsLoadingThumbnails(true);
    const thumbs = [];

    for (let i = 1; i <= pdfDoc.numPages; i++) {
      try {
        const page = await pdfDoc.getPage(i);
        const viewport = page.getViewport({ scale: 0.3 }); // Small scale for thumbnails
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        await page.render({
          canvasContext: context,
          viewport: viewport,
        }).promise;

        thumbs.push(canvas.toDataURL("image/jpeg", 0.6));
      } catch (error) {
        console.error(`Thumbnail generation failed for page ${i}:`, error);
        thumbs.push(null);
      }
    }

    setThumbnails(thumbs);
    setIsLoadingThumbnails(false);
    setShowThumbnails(true);
  };

  // Select page from thumbnail
  const selectPageFromThumbnail = async (pageNum) => {
    setShowThumbnails(false);
    setIsLoadingPage(true);
    setCurrentPage(pageNum);
    await renderPdfPage(pdfDoc, pageNum);
  };

  // Handle crop completion and add padding
  const handleCropDone = (dataUrl) => {
    // Add padding around the cropped image
    const img = new Image();
    img.onload = () => {
      const padding = 5; // Very minimal padding (5px on all sides)
      let finalWidth = img.width + (padding * 2);
      let finalHeight = img.height + (padding * 2);

      // Much smaller images for KakaoTalk (max 400x533 - 3:4 ratio)
      const maxWidth = 400;
      const maxHeight = 533;

      if (finalWidth > maxWidth || finalHeight > maxHeight) {
        const widthScale = maxWidth / finalWidth;
        const heightScale = maxHeight / finalHeight;
        const scale = Math.min(widthScale, heightScale);
        finalWidth = Math.round(finalWidth * scale);
        finalHeight = Math.round(finalHeight * scale);
      }

      const canvas = document.createElement("canvas");
      canvas.width = finalWidth;
      canvas.height = finalHeight;

      const ctx = canvas.getContext("2d");

      // Fill with white background
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, finalWidth, finalHeight);

      // Calculate scaled dimensions
      const scaledPadding = Math.round(padding * (finalWidth / (img.width + padding * 2)));
      const imgWidth = finalWidth - (scaledPadding * 2);
      const imgHeight = finalHeight - (scaledPadding * 2);

      // Draw cropped image in the center with high quality
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(img, scaledPadding, scaledPadding, imgWidth, imgHeight);

      // Convert to data URL
      const paddedDataUrl = canvas.toDataURL("image/png");
      setCroppedImage(paddedDataUrl);
    };
    img.src = dataUrl;
  };

  // Upload cropped image
  const handleUpload = async () => {
    if (!croppedImage || !problemData) return;

    setUploadStatus("uploading");
    setErrorMessage("");

    try {
      // Convert data URL to Blob
      const response = await fetch(croppedImage);
      const blob = await response.blob();

      // Map Korean subject to English for database
      const subjectMap = {
        "수1": "Math1",
        "수2": "Math2",
        "수학 1": "Math1",
        "수학 2": "Math2",
        "미적분": null,  // Not in DB constraint, send null
        "확률과통계": null,
        "기하": null
      };
      const dbSubject = subjectMap[metadata.subject] || null;

      // Create FormData with user-edited metadata
      const formData = new FormData();
      formData.append("file", blob, `${problemData.problem_id}.png`);
      formData.append("problem_id", problemData.problem_id);
      formData.append("year", problemData.year);
      formData.append("exam", problemData.exam);
      formData.append("question_no", problemData.question_no);
      formData.append("difficulty", metadata.difficulty);
      formData.append("category", metadata.unit);
      if (dbSubject) {
        formData.append("subject", dbSubject);  // Send only if Math1 or Math2
      }
      formData.append("answer", metadata.answer);
      formData.append("solution", metadata.solution);

      // Upload to server
      const uploadResponse = await fetch("/api/card/upload", {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (!uploadResponse.ok) throw new Error("Upload failed");

      const result = await uploadResponse.json();

      if (result.success) {
        setUploadStatus("success");
        // Auto-close after 1.5 seconds
        setTimeout(() => {
          onSuccess(result);
        }, 1500);
      } else {
        throw new Error(result.error || "Upload failed");
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("error");
      setErrorMessage(error.message || "업로드에 실패했습니다");
    }
  };

  // Drag and drop handlers
  const [dragging, setDragging] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const isImage = file.type.startsWith("image/");
    const isPDF = file.type === "application/pdf";

    if (!isImage && !isPDF) {
      setErrorMessage("이미지 또는 PDF 파일만 업로드 가능합니다");
      return;
    }

    if (isPDF) {
      await handlePDFUpload(file);
    } else {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImageSrc(event.target.result);
        setCroppedImage(null);
        setErrorMessage("");
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="crop-modal-overlay" onClick={onClose}>
      <div
        className="crop-modal-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="crop-modal-header">
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: "#1E293B" }}>
            이미지 크롭 {problemData && `- ${problemData.problem_id}`}
          </h2>
          <button
            className="crop-modal-close"
            onClick={onClose}
            title="닫기"
          >
            ×
          </button>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div
            style={{
              background: "#FEE2E2",
              color: "#991B1B",
              padding: "12px 16px",
              borderRadius: 8,
              marginBottom: 16,
              fontSize: 14,
            }}
          >
            {errorMessage}
          </div>
        )}

        {/* Content */}
        <div style={{ marginTop: 20 }}>
          {/* Step 1: Upload or use existing */}
          {!imageSrc && (
            <div
              style={{
                border: dragging ? "3px dashed #3B82F6" : "2px dashed #CBD5E1",
                borderRadius: 12,
                padding: 48,
                textAlign: "center",
                background: dragging ? "#EBF5FF" : "#F8FAFC",
                transition: "all 0.2s",
                cursor: "pointer",
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div style={{ fontSize: 48, marginBottom: 16 }}>📁</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#475569", marginBottom: 8 }}>
                이미지 또는 PDF를 드래그하거나 클릭하여 업로드
              </div>
              <div style={{ fontSize: 13, color: "#94A3B8" }}>
                PNG, JPG, GIF, PDF 형식 지원
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,application/pdf"
                style={{ display: "none" }}
                onChange={handleFileSelect}
              />
            </div>
          )}

          {/* Step 2: Crop */}
          {imageSrc && !croppedImage && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#475569", marginBottom: 8 }}>
                  마우스로 드래그하여 크롭할 영역을 선택하세요
                </div>
                <div style={{ fontSize: 13, color: "#94A3B8" }}>
                  영역을 선택한 후 "이 영역 크롭" 버튼을 클릭하세요
                </div>
              </div>

              {/* PDF Page Navigation */}
              {pdfDoc && totalPages > 1 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 12,
                    padding: "12px 16px",
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    borderRadius: 10,
                  }}>
                    <button
                      onClick={goToPrevPage}
                      disabled={currentPage <= 1 || isLoadingPage}
                      style={{
                        background: currentPage <= 1 ? "rgba(255,255,255,0.3)" : "white",
                        color: currentPage <= 1 ? "rgba(255,255,255,0.6)" : "#667eea",
                        border: "none",
                        borderRadius: 8,
                        padding: "8px 16px",
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: currentPage <= 1 ? "not-allowed" : "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      ◀ 이전
                    </button>

                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <select
                        value={currentPage}
                        onChange={(e) => goToPage(parseInt(e.target.value))}
                        disabled={isLoadingPage}
                        style={{
                          padding: "8px 12px",
                          borderRadius: 8,
                          border: "none",
                          fontSize: 14,
                          fontWeight: 600,
                          background: "white",
                          color: "#667eea",
                          cursor: "pointer",
                        }}
                      >
                        {Array.from({ length: totalPages }, (_, i) => (
                          <option key={i + 1} value={i + 1}>
                            {i + 1}페이지
                          </option>
                        ))}
                      </select>
                      <span style={{ color: "white", fontSize: 14, fontWeight: 500 }}>
                        / {totalPages}페이지
                      </span>
                    </div>

                    <button
                      onClick={goToNextPage}
                      disabled={currentPage >= totalPages || isLoadingPage}
                      style={{
                        background: currentPage >= totalPages ? "rgba(255,255,255,0.3)" : "white",
                        color: currentPage >= totalPages ? "rgba(255,255,255,0.6)" : "#667eea",
                        border: "none",
                        borderRadius: 8,
                        padding: "8px 16px",
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      다음 ▶
                    </button>

                    <button
                      onClick={generateThumbnails}
                      disabled={isLoadingThumbnails}
                      style={{
                        background: "rgba(255,255,255,0.9)",
                        color: "#667eea",
                        border: "none",
                        borderRadius: 8,
                        padding: "8px 16px",
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: "pointer",
                        transition: "all 0.2s",
                      }}
                    >
                      {isLoadingThumbnails ? "⏳ 생성중..." : "📋 전체 페이지 보기"}
                    </button>

                    {isLoadingPage && (
                      <span style={{ color: "white", fontSize: 13 }}>로딩 중...</span>
                    )}
                  </div>

                  {/* Thumbnail Grid View */}
                  {showThumbnails && thumbnails.length > 0 && (
                    <div style={{
                      marginTop: 16,
                      padding: 16,
                      background: "#F8FAFC",
                      borderRadius: 12,
                      border: "2px solid #E2E8F0",
                    }}>
                      <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 12,
                      }}>
                        <span style={{ fontSize: 14, fontWeight: 600, color: "#475569" }}>
                          페이지 선택 (클릭하여 해당 페이지로 이동)
                        </span>
                        <button
                          onClick={() => setShowThumbnails(false)}
                          style={{
                            background: "#E2E8F0",
                            color: "#64748B",
                            border: "none",
                            borderRadius: 6,
                            padding: "6px 12px",
                            fontSize: 13,
                            cursor: "pointer",
                          }}
                        >
                          ✕ 닫기
                        </button>
                      </div>
                      <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
                        gap: 12,
                        maxHeight: 400,
                        overflowY: "auto",
                        padding: 8,
                      }}>
                        {thumbnails.map((thumb, idx) => (
                          <div
                            key={idx}
                            onClick={() => selectPageFromThumbnail(idx + 1)}
                            style={{
                              cursor: "pointer",
                              border: currentPage === idx + 1 ? "3px solid #3B82F6" : "2px solid #E2E8F0",
                              borderRadius: 8,
                              overflow: "hidden",
                              background: "white",
                              transition: "all 0.2s",
                              boxShadow: currentPage === idx + 1 ? "0 4px 12px rgba(59,130,246,0.3)" : "none",
                            }}
                          >
                            {thumb ? (
                              <img
                                src={thumb}
                                alt={`Page ${idx + 1}`}
                                style={{
                                  width: "100%",
                                  display: "block",
                                }}
                              />
                            ) : (
                              <div style={{
                                height: 150,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                color: "#94A3B8",
                              }}>
                                로딩 실패
                              </div>
                            )}
                            <div style={{
                              padding: "6px 8px",
                              background: currentPage === idx + 1 ? "#3B82F6" : "#F1F5F9",
                              color: currentPage === idx + 1 ? "white" : "#64748B",
                              fontSize: 12,
                              fontWeight: 600,
                              textAlign: "center",
                            }}>
                              {idx + 1}페이지
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div style={{ textAlign: "center" }}>
                <CropCanvas
                  imageSrc={imageSrc}
                  pageIdx={0}
                  onCropDone={handleCropDone}
                />
              </div>
              <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  onClick={() => {
                    setImageSrc(null);
                    setCroppedImage(null);
                    setPdfDoc(null);
                    setTotalPages(0);
                    setCurrentPage(1);
                    setThumbnails([]);
                    setShowThumbnails(false);
                  }}
                  style={{
                    background: "#F1F5F9",
                    color: "#64748B",
                    border: "none",
                    borderRadius: 8,
                    padding: "10px 20px",
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  📷 다른 이미지/PDF 선택
                </button>
                {!pdfDoc && (
                  <button
                    onClick={() => {
                      const input = document.createElement('input');
                      input.type = 'file';
                      input.accept = 'application/pdf';
                      input.onchange = (e) => {
                        const file = e.target.files?.[0];
                        if (file) handlePDFUpload(file);
                      };
                      input.click();
                    }}
                    style={{
                      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      padding: "10px 20px",
                      fontSize: 14,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    📄 PDF에서 페이지 선택
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Preview and Upload */}
          {croppedImage && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#475569", marginBottom: 8 }}>
                  크롭 결과 미리보기
                </div>
                <div style={{ fontSize: 13, color: "#94A3B8" }}>
                  메타데이터를 확인/수정하고 업로드하세요
                </div>
              </div>
              <div
                style={{
                  textAlign: "center",
                  background: "#F8FAFC",
                  borderRadius: 12,
                  padding: 24,
                  marginBottom: 20,
                }}
              >
                <img
                  src={croppedImage}
                  alt="Cropped preview"
                  style={{
                    maxWidth: "100%",
                    maxHeight: 400,
                    borderRadius: 8,
                    boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
                  }}
                />
              </div>

              {/* Metadata Form */}
              <div style={{
                background: "#F8FAFC",
                borderRadius: 12,
                padding: 20,
                marginBottom: 20,
              }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#475569", marginBottom: 16 }}>
                  문제 정보 입력
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div>
                    <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 6 }}>
                      과목
                    </label>
                    <select
                      value={metadata.subject}
                      onChange={(e) => setMetadata({...metadata, subject: e.target.value})}
                      style={{
                        width: "100%",
                        padding: "10px 12px",
                        borderRadius: 8,
                        border: "1px solid #CBD5E1",
                        fontSize: 14,
                        background: "white"
                      }}
                    >
                      <option value="수1">수학 1</option>
                      <option value="수2">수학 2</option>
                      <option value="미적분">미적분</option>
                      <option value="확률과통계">확률과 통계</option>
                      <option value="기하">기하</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 6 }}>
                      난이도 (점수)
                    </label>
                    <select
                      value={metadata.difficulty}
                      onChange={(e) => setMetadata({...metadata, difficulty: e.target.value})}
                      style={{
                        width: "100%",
                        padding: "10px 12px",
                        borderRadius: 8,
                        border: "1px solid #CBD5E1",
                        fontSize: 14,
                        background: "white"
                      }}
                    >
                      <option value="2점">2점</option>
                      <option value="3점">3점</option>
                      <option value="4점">4점</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 6 }}>
                      단원
                    </label>
                    <select
                      value={metadata.unit}
                      onChange={(e) => setMetadata({...metadata, unit: e.target.value})}
                      style={{
                        width: "100%",
                        padding: "10px 12px",
                        borderRadius: 8,
                        border: "1px solid #CBD5E1",
                        fontSize: 14,
                        background: "white"
                      }}
                    >
                      <option value="이차함수">이차함수</option>
                      <option value="삼각함수">삼각함수</option>
                      <option value="수열">수열</option>
                      <option value="미분">미분</option>
                      <option value="적분">적분</option>
                      <option value="확률">확률</option>
                      <option value="통계">통계</option>
                      <option value="기하">기하</option>
                      <option value="지수로그">지수로그</option>
                      <option value="집합">집합</option>
                      <option value="함수">함수</option>
                      <option value="기타">기타</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 6 }}>
                      정답
                    </label>
                    <input
                      type="text"
                      value={metadata.answer}
                      onChange={(e) => setMetadata({...metadata, answer: e.target.value})}
                      placeholder="예: ①, 3, 1/2"
                      style={{
                        width: "100%",
                        padding: "10px 12px",
                        borderRadius: 8,
                        border: "1px solid #CBD5E1",
                        fontSize: 14,
                        background: "white"
                      }}
                    />
                  </div>
                </div>
                <div style={{ marginTop: 16 }}>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 6 }}>
                    해설 (선택사항)
                  </label>
                  <textarea
                    value={metadata.solution}
                    onChange={(e) => setMetadata({...metadata, solution: e.target.value})}
                    placeholder="문제 해설을 입력하세요..."
                    rows={3}
                    style={{
                      width: "100%",
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: "1px solid #CBD5E1",
                      fontSize: 14,
                      background: "white",
                      resize: "vertical",
                      fontFamily: "inherit"
                    }}
                  />
                </div>
              </div>

              {uploadStatus === "success" && (
                <div
                  style={{
                    background: "#D1FAE5",
                    color: "#065F46",
                    padding: "12px 16px",
                    borderRadius: 8,
                    marginBottom: 16,
                    fontSize: 14,
                    textAlign: "center",
                  }}
                >
                  ✓ 업로드 완료! 모달이 곧 닫힙니다...
                </div>
              )}

              <div style={{ display: "flex", gap: 12 }}>
                <button
                  onClick={handleUpload}
                  disabled={uploadStatus === "uploading" || uploadStatus === "success"}
                  style={{
                    flex: 1,
                    background: uploadStatus === "uploading" ? "#94A3B8" : "#10B981",
                    color: "#fff",
                    border: "none",
                    borderRadius: 8,
                    padding: "12px 24px",
                    fontSize: 15,
                    fontWeight: 700,
                    cursor: uploadStatus === "uploading" ? "not-allowed" : "pointer",
                  }}
                >
                  {uploadStatus === "uploading" ? "⏳ 업로드 중..." : "📤 업로드 & 저장"}
                </button>
                <button
                  onClick={() => setCroppedImage(null)}
                  disabled={uploadStatus === "uploading" || uploadStatus === "success"}
                  style={{
                    background: "#F1F5F9",
                    color: "#64748B",
                    border: "none",
                    borderRadius: 8,
                    padding: "12px 24px",
                    fontSize: 15,
                    fontWeight: 600,
                    cursor: uploadStatus === "uploading" ? "not-allowed" : "pointer",
                  }}
                >
                  다시 크롭
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Export to window for use in admin page
window.CropModal = CropModal;
