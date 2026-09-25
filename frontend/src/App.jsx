import { useState } from "react";
import "./App.css";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { createWorker } from "tesseract.js";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

/* =========================================================
   CONFIGURATION
========================================================= */

const API_BASE_URL = "http://127.0.0.1:8000";


/* =========================================================
   LOGO
========================================================= */

function ShieldLogo() {
  return (
    <div className="logo-box">
      <span>🛡️</span>
    </div>
  );
}


/* =========================================================
   THEME TOGGLE
========================================================= */

function ThemeToggle({ theme, setTheme }) {
  const isDark = theme === "dark";

  return (
    <button
      className="theme-toggle"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      <span className="theme-icon">{isDark ? "☀️" : "🌙"}</span>

      <span>{isDark ? "Light" : "Dark"}</span>

      <span
        className={`toggle-switch ${isDark ? "dark-active" : ""}`}
      >
        <span />
      </span>
    </button>
  );
}


/* =========================================================
   HEADER
========================================================= */

function Header({ theme, setTheme }) {
  return (
    <header className="header">
      <div className="brand">
        <ShieldLogo />

        <div>
          <h2>
            Scam<span>Shield</span>
          </h2>

          <p>Verify Before You Trust</p>
        </div>
      </div>

      <ThemeToggle
        theme={theme}
        setTheme={setTheme}
      />
    </header>
  );
}


/* =========================================================
   DOCUMENT EXTRACTION / OCR HELPERS
========================================================= */

const MAX_ANALYSIS_TEXT = 5000;
const MAX_FILE_SIZE_MB = 15;
const MAX_PDF_PAGES = 10;

function limitAnalysisText(value) {
  return String(value || "").trim().slice(0, MAX_ANALYSIS_TEXT);
}

async function extractImageText(file, onProgress) {
  const worker = await createWorker("eng");
  try {
    onProgress?.("OCR: reading image…");
    const result = await worker.recognize(file);
    return (result?.data?.text || "").trim();
  } finally {
    await worker.terminate();
  }
}

async function extractPdfText(file, onProgress) {
  const buffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pageCount = Math.min(pdf.numPages, MAX_PDF_PAGES);
  const parts = [];

  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    onProgress?.(`PDF: extracting page ${pageNumber}/${pageCount}…`);
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();
    const pageText = content.items
      .map((item) => item.str || "")
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();

    if (pageText) {
      parts.push(pageText);
    }
  }

  return {
    text: parts.join("\n\n").trim(),
    pageCount: pdf.numPages,
    extractedPages: pageCount,
  };
}

async function renderPdfPageToCanvas(page, scale = 1.5) {
  const viewport = page.getViewport({ scale });
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", { willReadFrequently: true });

  canvas.width = Math.ceil(viewport.width);
  canvas.height = Math.ceil(viewport.height);

  await page.render({
    canvasContext: context,
    viewport,
  }).promise;

  return canvas;
}

async function extractScannedPdfText(file, onProgress) {
  const buffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pageCount = Math.min(pdf.numPages, MAX_PDF_PAGES);
  const worker = await createWorker("eng");
  const parts = [];

  try {
    for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
      onProgress?.(`OCR: scanning PDF page ${pageNumber}/${pageCount}…`);
      const page = await pdf.getPage(pageNumber);
      const canvas = await renderPdfPageToCanvas(page, 1.5);
      const result = await worker.recognize(canvas);
      const pageText = (result?.data?.text || "").trim();

      if (pageText) {
        parts.push(pageText);
      }

      canvas.width = 1;
      canvas.height = 1;
    }
  } finally {
    await worker.terminate();
  }

  return {
    text: parts.join("\n\n").trim(),
    pageCount: pdf.numPages,
    extractedPages: pageCount,
  };
}

async function extractFileText(file, inputType, onProgress) {
  if (!file) {
    throw new Error("Please select a PDF or image file first.");
  }

  const sizeMb = file.size / (1024 * 1024);
  if (sizeMb > MAX_FILE_SIZE_MB) {
    throw new Error(`File is too large. Please use a file under ${MAX_FILE_SIZE_MB} MB.`);
  }

  if (inputType === "Image") {
    onProgress?.("OCR: starting image text extraction…");
    const text = await extractImageText(file, onProgress);
    if (!text) {
      throw new Error("No readable text was found in this image.");
    }

    return {
      text: limitAnalysisText(text),
      inputType: "Image",
      ocrStatus: "Completed",
      sourceFileName: file.name,
    };
  }

  if (inputType === "PDF") {
    const extracted = await extractPdfText(file, onProgress);
    let text = extracted.text;
    let ocrStatus = "Text extracted";

    // Scanned/image-only PDFs normally have little or no text layer.
    if (text.length < 40) {
      onProgress?.("PDF has little/no text layer. Starting OCR…");
      const ocr = await extractScannedPdfText(file, onProgress);
      text = ocr.text;
      ocrStatus = "OCR completed";
    }

    if (!text) {
      throw new Error("Could not extract readable text from this PDF.");
    }

    return {
      text: limitAnalysisText(text),
      inputType: "PDF",
      ocrStatus,
      sourceFileName: file.name,
      pageCount: extracted.pageCount,
    };
  }

  throw new Error("Unsupported input type.");
}


/* =========================================================
   STEP 1 - INPUT SCREEN
========================================================= */

function StepOne({ onAnalyze, loading, processingMessage }) {
  const [activeTab, setActiveTab] = useState("text");
  const [text, setText] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFile = (event, type) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const expectedPdf = type === "pdf";
    const valid = expectedPdf
      ? file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
      : file.type.startsWith("image/") || /\.(png|jpe?g|webp|bmp|gif)$/i.test(file.name);

    if (!valid) {
      alert(expectedPdf ? "Please select a PDF file." : "Please select an image file.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      alert(`Please select a file smaller than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    setSelectedFile(file);
    setActiveTab(expectedPdf ? "pdf" : "image");
    setText("");
  };

  const handleAnalyze = () => {
    if (activeTab === "text") {
      const cleanText = limitAnalysisText(text);

      if (!cleanText) {
        alert("Please paste the job offer, recruitment message or email text.");
        return;
      }

      onAnalyze({
        text: cleanText,
        inputType: "Text",
        ocrStatus: "Not required",
        sourceFileName: "",
      });
      return;
    }

    if (!selectedFile) {
      alert(`Please select a ${activeTab === "pdf" ? "PDF" : "image"} file first.`);
      return;
    }

    onAnalyze({
      file: selectedFile,
      inputType: activeTab === "pdf" ? "PDF" : "Image",
    });
  };

  const useExample = (type) => {
    const examples = {
      email:
        "Congratulations! You have been selected for the position of Software Developer. Pay ₹5,000 registration fee within 24 hours to confirm your joining. Contact us only through WhatsApp.",
      whatsapp:
        "Hello candidate, you are directly selected for our company. No interview is required. Please pay the processing fee of ₹2,500 through UPI immediately.",
      genuine:
        "Dear Candidate, your application has been shortlisted for the Software Developer position. Please attend the scheduled technical interview through our official recruitment portal.",
      upi:
        "URGENT: Your job offer will expire today. Send ₹3,000 through UPI immediately to secure your position.",
    };

    setActiveTab("text");
    setText(examples[type]);
    setSelectedFile(null);
  };

  return (
    <main className="step-one">
      <section className="hero">
        <div className="ai-badge">✨ AI-Powered Analysis</div>

        <h1>
          Verify Before
          <br />
          You <span>Trust</span>
        </h1>

        <p className="hero-description">
          Analyze job offers, recruitment messages, PDFs and screenshots to detect
          potential scams and suspicious recruitment patterns.
        </p>

        <div className="hero-pills">
          <div>🔍 Detect fraud patterns</div>
          <div>🏢 Check company details</div>
          <div>🛡️ Stay safe from scams</div>
        </div>
      </section>

      <section className="analyzer-card">
        <div className="input-tabs">
          <button
            type="button"
            className={activeTab === "text" ? "active" : ""}
            onClick={() => {
              setActiveTab("text");
              setSelectedFile(null);
            }}
            disabled={loading}
          >
            🔍 <span>Paste Text</span>
          </button>

          <label className={activeTab === "pdf" ? "active" : ""}>
            📄 <span>Upload PDF</span>
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => handleFile(e, "pdf")}
              disabled={loading}
              hidden
            />
          </label>

          <label className={activeTab === "image" ? "active" : ""}>
            🖼️ <span>Upload Image</span>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleFile(e, "image")}
              disabled={loading}
              hidden
            />
          </label>
        </div>

        <div className="quick-buttons">
          <button type="button" onClick={() => useExample("email")} disabled={loading}>
            📌 Job Offer Email
          </button>
          <button type="button" onClick={() => useExample("whatsapp")} disabled={loading}>
            💬 WhatsApp Message
          </button>
          <button type="button" onClick={() => useExample("genuine")} disabled={loading}>
            📄 Genuine Offer
          </button>
          <button type="button" onClick={() => useExample("upi")} disabled={loading}>
            ⚠️ Urgent UPI
          </button>
        </div>

        {activeTab === "text" && (
          <div className="text-section">
            <label>Job offer text</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value.slice(0, MAX_ANALYSIS_TEXT))}
              onPaste={(e) => {
                const pastedText = e.clipboardData?.getData("text") || "";
                if (pastedText) {
                  e.preventDefault();
                  const target = e.currentTarget;
                  const start = target.selectionStart ?? text.length;
                  const end = target.selectionEnd ?? text.length;
                  const nextText = `${text.slice(0, start)}${pastedText}${text.slice(end)}`
                    .slice(0, MAX_ANALYSIS_TEXT);
                  setText(nextText);
                }
              }}
              placeholder="Paste your job offer, email or recruitment message here..."
              maxLength={MAX_ANALYSIS_TEXT}
              disabled={loading}
              spellCheck="true"
            />
            <div className="character-count">{text.length}/{MAX_ANALYSIS_TEXT}</div>
          </div>
        )}

        {(activeTab === "pdf" || activeTab === "image") && (
          <div className="file-upload-box">
            <div className="upload-icon">{activeTab === "pdf" ? "📄" : "🖼️"}</div>

            <h3>
              {selectedFile
                ? selectedFile.name
                : activeTab === "pdf"
                ? "Upload Job Offer PDF"
                : "Upload Job Offer Screenshot"}
            </h3>

            <p>
              {selectedFile
                ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                : activeTab === "pdf"
                ? `Select a PDF document for extraction/OCR (max ${MAX_FILE_SIZE_MB} MB)`
                : `Select a screenshot or image for OCR (max ${MAX_FILE_SIZE_MB} MB)`}
            </p>

            <label className="choose-file">
              Choose File
              <input
                type="file"
                accept={activeTab === "pdf" ? ".pdf,application/pdf" : "image/*"}
                onChange={(e) => handleFile(e, activeTab)}
                disabled={loading}
                hidden
              />
            </label>
          </div>
        )}

        {selectedFile && (
          <div className="selected-file">
            ✓ {selectedFile.name}
            <button
              type="button"
              onClick={() => {
                setSelectedFile(null);
                setActiveTab("text");
                setText("");
              }}
              disabled={loading}
            >
              Remove
            </button>
          </div>
        )}

        {loading && processingMessage && (
          <p style={{ textAlign: "center", margin: "12px 0", fontWeight: 600 }}>
            ⏳ {processingMessage}
          </p>
        )}

        <button
          type="button"
          className="analyze-button"
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? "⏳ Analyzing..." : "🔍  Analyze Now →"}
        </button>

        <p className="privacy-note">
          🔒 Text is sent to the ScamShield backend for rule-based analysis. Files are
          processed in the browser and their extracted text is sent for analysis.
        </p>
      </section>

      <section className="features">
        <FeatureCard icon="🔍" title="Detect Suspicious Patterns" text="Find red flags in job offers and recruitment messages." type="blue" />
        <FeatureCard icon="🏢" title="Verify Company Details" text="Check basic company and domain information." type="purple" />
        <FeatureCard icon="📄" title="Analyze Documents" text="Extract and analyze text from PDFs and screenshots." type="green" />
        <FeatureCard icon="📊" title="Get Instant Results" text="Receive risk score, evidence and safety recommendations." type="pink" />
      </section>
    </main>
  );
}


/* =========================================================
   FEATURE CARD
========================================================= */

function FeatureCard({
  icon,
  title,
  text,
  type,
}) {
  return (
    <div className="feature-card">

      <div className={`feature-icon ${type}`}>
        {icon}
      </div>

      <h3>{title}</h3>

      <p>{text}</p>

    </div>
  );
}


/* =========================================================
   STEP 2 - RESULT SCREEN
========================================================= */

function StepTwo({
  analysisData,
  onAnalyzeAnother,
}) {

  const data =
    analysisData?.data ||
    analysisData ||
    {};

  const riskScore =
    Number(data.risk_score ?? 0);

  const riskLevel =
    data.risk_level || "Unknown";

  const totalChecks =
    Number(data.total_checks ?? 0);

  const redFlagsCount =
    Number(
      data.red_flags_count ??
      data.red_flags?.length ??
      0
    );

  const findings =
    Array.isArray(data.findings)
      ? data.findings
      : [];

  const recommendations =
    Array.isArray(data.recommendations)
      ? data.recommendations
      : [];

  const suspiciousDomains =
    Array.isArray(data.suspicious_domains)
      ? data.suspicious_domains
      : [];

  const extracted =
    data.extracted_information || {};

  const quickSummary =
    data.quick_summary || {};


  /* -------------------------------------------------------
     Risk Helpers
  ------------------------------------------------------- */

  const normalizedRisk =
    riskLevel.toLowerCase();

  const isHigh =
    normalizedRisk.includes("high");

  const isMedium =
    normalizedRisk.includes("medium");

  const isLow =
    normalizedRisk.includes("low");


  let riskIcon = "⚠️";

  if (isLow) {
    riskIcon = "🟢";
  } else if (isMedium) {
    riskIcon = "🟡";
  }


  const riskTitle = isHigh
    ? "High Risk Indicators Detected"
    : isMedium
    ? "Medium Risk Indicators Detected"
    : isLow
    ? "Low Risk Indicators"
    : "Analysis Completed";


  const riskDescription = isHigh
    ? "Multiple suspicious indicators were detected in this recruitment message. Review the evidence carefully before taking any action."
    : isMedium
    ? "Some suspicious indicators were detected. Verify the recruiter, company and offer before proceeding."
    : isLow
    ? "No major scam indicators were detected by the current rule-based checks. Continue to verify the source independently."
    : "The analysis has been completed. Review the detected findings below.";

  // Dynamic risk ring: the filled arc is calculated from the backend score.
  const safeRiskScore = Math.max(0, Math.min(100, riskScore));
  const riskAngle = `${safeRiskScore * 3.6}deg`;
  const riskRingColor = isHigh
    ? "#f04f55"
    : isMedium
    ? "#f4a82e"
    : "#438ce8";


  /* -------------------------------------------------------
     Download Report
  ------------------------------------------------------- */

  const downloadReport = () => {

    const report = `
SCAMSHIELD ANALYSIS REPORT
==========================

Risk Score: ${riskScore}/100
Risk Level: ${riskLevel}

Total Checks: ${totalChecks}
Red Flags Detected: ${redFlagsCount}

FINDINGS
--------

${
  findings.length
    ? findings
        .map(
          (item, index) =>
            `${index + 1}. ${item.category || "Unknown"}
Evidence: ${item.detected_text || item.evidence || "N/A"}
Severity: ${item.severity || "N/A"}
Explanation: ${item.explanation || "N/A"}
Score: ${item.score ?? "N/A"}
`
        )
        .join("\n")
    : "No findings detected."
}

RECOMMENDATIONS
---------------

${
  recommendations.length
    ? recommendations
        .map(
          (item, index) =>
            `${index + 1}. ${item}`
        )
        .join("\n")
    : "No specific recommendations."
}

SUSPICIOUS DOMAINS
------------------

${
  suspiciousDomains.length
    ? suspiciousDomains.join("\n")
    : "None detected."
}

Generated by ScamShield
`;

    const blob =
      new Blob([report], {
        type: "text/plain",
      });

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download =
      "scamshield-analysis-report.txt";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };


  return (
    <main className="step-two">

      {/* RESULT HEADER */}
      <div className="result-header">

        <button
          className="analyze-another"
          onClick={onAnalyzeAnother}
        >
          ← &nbsp; Analyze Another
        </button>


        <div className="result-title">

          <h2>
            Analysis Result
          </h2>

          <p>
            Here is the detailed analysis of
            the provided job offer.
          </p>

        </div>


        <div className="result-actions">

          <span>
            🕐 Analyzed just now
          </span>

          <button
            className="download-button"
            onClick={downloadReport}
          >
            ↓ &nbsp; Download Report
          </button>

        </div>

      </div>


      {/* =====================================================
          TOP RESULT CARDS
      ====================================================== */}

      <section className="result-grid">

        {/* RISK SCORE */}
        <div className="risk-score-card">

          <div
            className="score-ring"
            style={{
              "--risk-angle": riskAngle,
              "--risk-ring-color": riskRingColor,
            }}
            aria-label={`Risk score ${safeRiskScore} out of 100`}
          >

            <div>

              <strong>
                {riskScore}
              </strong>

              <span>
                / 100
              </span>

              <small>
                Risk Score
              </small>

            </div>

          </div>


          <div className="risk-badge">
            {riskIcon} {riskLevel}
          </div>

        </div>


        {/* RISK MESSAGE */}
        <div className="risk-message">

          <div className="risk-message-icon">
            {riskIcon}
          </div>

          <div>

            <h2>
              {riskTitle}
            </h2>

            <p>
              {riskDescription}
            </p>

          </div>

        </div>


        {/* QUICK SUMMARY */}
        <div className="quick-summary">

          <h3>
            📄 Quick Summary
          </h3>

          <SummaryRow
            label="Total Checks Performed"
            value={totalChecks}
          />

          <SummaryRow
            label="Red Flags Detected"
            value={redFlagsCount}
          />

          <SummaryRow
            label="Risk Score"
            value={`${riskScore} / 100`}
            highlight
          />

          <SummaryRow
            label="Risk Level"
            value={riskLevel}
            highlight
          />

          <SummaryRow
            label="Analysis Type"
            value={
              data.analysis_type ||
              "Rule Based"
            }
          />

        </div>

      </section>


      {/* =====================================================
          INDICATORS
      ====================================================== */}

      <section className="indicator-grid">

        <Indicator
          icon="₹"
          title="Financial Demand"
          findings={findings}
          keywords={[
            "financial",
            "payment",
            "money",
            "fee",
            "demand",
          ]}
        />

        <Indicator
          icon="◷"
          title="Urgency Pressure"
          findings={findings}
          keywords={[
            "urgency",
            "urgent",
            "deadline",
          ]}
        />

        <Indicator
          icon="🔗"
          title="Suspicious Domain"
          findings={findings}
          keywords={[
            "domain",
            "website",
            "url",
          ]}
        />

        <Indicator
          icon="👥"
          title="Direct Selection"
          findings={findings}
          keywords={[
            "direct selection",
            "selection",
          ]}
        />

        <Indicator
          icon="💬"
          title="Unusual Communication"
          findings={findings}
          keywords={[
            "communication",
            "telegram",
            "whatsapp",
            "unusual",
          ]}
        />

      </section>


      {/* =====================================================
          EVIDENCE TABLE
      ====================================================== */}

      <section className="dashboard-card evidence-card">

        <SectionTitle
          icon="⚑"
          title="Detected Risk Indicators & Evidence"
        />

        <div className="table-wrapper">

          <table>

            <thead>

              <tr>

                <th>#</th>
                <th>Category</th>
                <th>Detected Text / Evidence</th>
                <th>Explanation</th>
                <th>Severity</th>

              </tr>

            </thead>


            <tbody>

              {findings.length === 0 ? (

                <tr>

                  <td
                    colSpan="5"
                    style={{
                      textAlign: "center",
                      padding: "30px",
                    }}
                  >
                    No suspicious findings detected.
                  </td>

                </tr>

              ) : (

                findings.map(
                  (finding, index) => (

                    <EvidenceRow
                      key={index}
                      n={index + 1}
                      category={
                        finding.category ||
                        "Unknown"
                      }
                      evidence={
                        finding.detected_text ||
                        finding.evidence ||
                        "Not available"
                      }
                      explanation={
                        finding.explanation ||
                        "No explanation available."
                      }
                      severity={
                        finding.severity ||
                        "Low"
                      }
                    />

                  )
                )

              )}

            </tbody>

          </table>

        </div>

      </section>


      {/* =====================================================
          INFORMATION CARDS
      ====================================================== */}

      <section className="three-column">

        {/* EXTRACTED INFORMATION */}
        <InfoCard
          title="🗃️ Extracted Information"
          type="blue"
        >

          <InfoRow
            label="Email Addresses"
            value={formatArray(
              extracted.email_addresses
            )}
          />

          <InfoRow
            label="Web Links"
            value={formatArray(
              extracted.web_links
            )}
          />

          <InfoRow
            label="Phone Numbers"
            value={formatArray(
              extracted.phone_numbers
            )}
          />

          <InfoRow
            label="Monetary Amounts"
            value={formatArray(
              extracted.monetary_amounts
            )}
          />

        </InfoCard>


        {/* DOCUMENT */}
        <InfoCard
          title="📄 PDF / Image Document Analysis"
          type="purple"
        >

          <InfoRow
            label="Input Type"
            value={
              analysisData?.inputType ||
              "Text"
            }
          />

          <InfoRow
            label="Analysis Type"
            value={
              data.analysis_type ||
              "Rule Based"
            }
          />

          <InfoRow
            label="OCR Status"
            value={analysisData?.ocrStatus || "Not required"}
          />

          {analysisData?.sourceFileName && (
            <InfoRow
              label="File Name"
              value={analysisData.sourceFileName}
            />
          )}

          {analysisData?.pageCount && (
            <InfoRow
              label="PDF Pages"
              value={analysisData.pageCount}
            />
          )}

          <div className="info-warning">
            {analysisData?.inputType === "Text"
              ? "ℹ️ Text was sent directly to the ScamShield analysis API."
              : "✓ Text was extracted in the browser and then analyzed by the ScamShield backend."}
          </div>

        </InfoCard>


        {/* DOMAIN */}
        <InfoCard
          title="🏢 Company & Domain Verification"
          type="blue"
        >

          <InfoRow
            label="Suspicious Domains"
            value={
              suspiciousDomains.length
                ? suspiciousDomains.join(", ")
                : "None detected"
            }
          />

          <InfoRow
            label="Domain Check"
            value={
              suspiciousDomains.length
                ? "Review Required"
                : "No suspicious domain detected"
            }
          />

          <InfoRow
            label="Company Verification"
            value="Coming Soon"
          />

          <InfoRow
            label="MCA Verification"
            value="Coming Soon"
          />

          <InfoRow
            label="Address Verification"
            value="Coming Soon"
          />

        </InfoCard>

      </section>


      {/* =====================================================
          ANALYTICS
      ====================================================== */}

      <section className="analytics-layout">

        <div className="dashboard-card analytics-card">

          <SectionTitle
            icon="📊"
            title="Analytics Overview"
          />


          <div className="analytics-grid">

            {/* RISK SCORE */}
            <div className="chart-box">

              <h4>
                Current Risk Score
              </h4>

              <div className="bar-chart">

                <div className="bar-column">

                  <span>
                    {riskScore}
                  </span>

                  <div
                    className={
                      isHigh
                        ? "bar high"
                        : isMedium
                        ? "bar medium"
                        : "bar low"
                    }
                    style={{
                      height: `${Math.max(
                        10,
                        Math.min(
                          100,
                          riskScore
                        )
                      )}%`,
                    }}
                  />

                  <small>
                    Score
                  </small>

                </div>

              </div>

            </div>


            {/* CHECKS */}
            <div className="chart-box">

              <h4>
                Analysis Summary
              </h4>

              <div className="donut-area">

                <div className="donut">

                  <div>

                    <strong>
                      {totalChecks}
                    </strong>

                    <span>
                      Total Checks
                    </span>

                  </div>

                </div>


                <div className="legend">

                  <span>
                    🚩 Red Flags&nbsp;
                    {redFlagsCount}
                  </span>

                  <span>
                    🔍 Checks&nbsp;
                    {totalChecks}
                  </span>

                  <span>
                    📊 Score&nbsp;
                    {riskScore}/100
                  </span>

                </div>

              </div>

            </div>


            {/* FINDINGS */}
            <div className="chart-box">

              <h4>
                Findings by Severity
              </h4>

              <div className="horizontal-bars">

                <ChartBar
                  label="High"
                  value={
                    countSeverity(
                      findings,
                      "high"
                    )
                  }
                  width={`${getSeverityWidth(
                    findings,
                    "high"
                  )}%`}
                />

                <ChartBar
                  label="Medium"
                  value={
                    countSeverity(
                      findings,
                      "medium"
                    )
                  }
                  width={`${getSeverityWidth(
                    findings,
                    "medium"
                  )}%`}
                />

                <ChartBar
                  label="Low"
                  value={
                    countSeverity(
                      findings,
                      "low"
                    )
                  }
                  width={`${getSeverityWidth(
                    findings,
                    "low"
                  )}%`}
                />

              </div>

            </div>

          </div>

        </div>


        {/* =================================================
            RECOMMENDATIONS
        ================================================== */}

        <div className="dashboard-card recommendations">

          <SectionTitle
            icon="🛡️"
            title="Safety Recommendations"
          />

          <ol>

            {recommendations.length === 0 ? (

              <li>
                No major recommendations were
                generated by the current analysis.
              </li>

            ) : (

              recommendations.map(
                (recommendation, index) => (

                  <li key={index}>
                    {recommendation}
                  </li>

                )
              )

            )}

          </ol>

        </div>

      </section>

    </main>
  );
}


/* =========================================================
   SUMMARY ROW
========================================================= */

function SummaryRow({
  label,
  value,
  highlight,
}) {
  return (
    <div className="summary-row">

      <span>{label}</span>

      <strong
        className={
          highlight
            ? "highlight"
            : ""
        }
      >
        {value}
      </strong>

    </div>
  );
}


/* =========================================================
   INDICATOR
========================================================= */

function Indicator({
  icon,
  title,
  findings,
  keywords,
}) {

  const matchedFindings =
    findings.filter((finding) => {

      const category =
        String(
          finding.category || ""
        ).toLowerCase();

      const evidence =
        String(
          finding.detected_text ||
          finding.evidence ||
          ""
        ).toLowerCase();

      return keywords.some(
        (keyword) =>
          category.includes(
            keyword.toLowerCase()
          ) ||
          evidence.includes(
            keyword.toLowerCase()
          )
      );
    });


  const detected =
    matchedFindings.length > 0;

  const issueText =
    matchedFindings.length === 1
      ? "1 issue"
      : `${matchedFindings.length} issues`;


  return (
    <div
      className={`indicator ${
        !detected
          ? "safe-indicator"
          : ""
      }`}
    >

      <div className="indicator-icon">
        {icon}
      </div>

      <div>

        <h4>
          {title}
        </h4>

        <span
          className={`status ${
            !detected
              ? "safe"
              : ""
          }`}
        >
          {detected
            ? "⚠️ Detected"
            : "✓ Not Detected"}
        </span>

        <p>
          {issueText}
        </p>

      </div>

    </div>
  );
}


/* =========================================================
   SECTION TITLE
========================================================= */

function SectionTitle({
  icon,
  title,
}) {
  return (
    <div className="section-title">

      <span>
        {icon}
      </span>

      <h3>
        {title}
      </h3>

    </div>
  );
}


/* =========================================================
   EVIDENCE ROW
========================================================= */

function EvidenceRow({
  n,
  category,
  evidence,
  explanation,
  severity,
}) {

  const safeSeverity =
    String(
      severity || "Low"
    );

  return (
    <tr>

      <td>
        {n}
      </td>

      <td>
        {category}
      </td>

      <td>
        {evidence}
      </td>

      <td>
        {explanation}
      </td>

      <td>

        <span
          className={`severity ${safeSeverity.toLowerCase()}`}
        >
          {safeSeverity}
        </span>

      </td>

    </tr>
  );
}


/* =========================================================
   INFO CARD
========================================================= */

function InfoCard({
  title,
  children,
  type,
}) {
  return (
    <div className="dashboard-card info-card">

      <SectionTitle
        icon=""
        title={title}
      />

      <div
        className={`info-content ${type}`}
      >
        {children}
      </div>

    </div>
  );
}


/* =========================================================
   INFO ROW
========================================================= */

function InfoRow({
  label,
  value,
}) {
  return (
    <div className="info-row">

      <span>
        {label}
      </span>

      <strong>
        {value || "None"}
      </strong>

    </div>
  );
}


/* =========================================================
   CHART BAR
========================================================= */

function ChartBar({
  label,
  value,
  width,
}) {
  return (
    <div className="chart-bar-row">

      <span>
        {label}
      </span>

      <div className="chart-track">

        <div
          style={{
            width:
              width || "0%",
          }}
        />

      </div>

      <b>
        {value}
      </b>

    </div>
  );
}


/* =========================================================
   UTILITY FUNCTIONS
========================================================= */

function formatArray(value) {

  if (!Array.isArray(value)) {
    return value || "None detected";
  }

  if (value.length === 0) {
    return "None detected";
  }

  return value.join(", ");
}


function countSeverity(
  findings,
  severity
) {
  return findings.filter(
    (finding) =>
      String(
        finding.severity || ""
      ).toLowerCase() ===
      severity.toLowerCase()
  ).length;
}


function getSeverityWidth(
  findings,
  severity
) {

  const count =
    countSeverity(
      findings,
      severity
    );

  if (findings.length === 0) {
    return 0;
  }

  return Math.max(
    5,
    Math.round(
      (count /
        findings.length) *
        100
    )
  );
}


/* =========================================================
   MAIN APP
========================================================= */

function App() {

  const [theme, setTheme] =
    useState("dark");

  const [step, setStep] =
    useState(1);

  const [analysisData, setAnalysisData] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [processingMessage, setProcessingMessage] =
    useState("");


  /* -------------------------------------------------------
     EXTRACT FILE -> CALL BACKEND
  ------------------------------------------------------- */

  const handleAnalyze = async ({
    text,
    inputType = "Text",
    file = null,
    ocrStatus = "Not required",
    sourceFileName = "",
    pageCount = null,
  }) => {
    setLoading(true);
    setAnalysisData(null);

    try {
      let analysisText = limitAnalysisText(text);
      let documentInfo = {
        inputType,
        ocrStatus,
        sourceFileName,
        pageCount,
      };

      if (file) {
        setProcessingMessage(`Preparing ${inputType.toLowerCase()}…`);

        const extracted = await extractFileText(
          file,
          inputType,
          (message) => setProcessingMessage(message)
        );

        analysisText = extracted.text;
        documentInfo = {
          ...documentInfo,
          ...extracted,
        };
      }

      if (!analysisText?.trim()) {
        throw new Error("No readable text was found to analyze.");
      }

      setProcessingMessage("Sending extracted text to ScamShield backend…");

      const response = await fetch(`${API_BASE_URL}/analysis/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          text: analysisText.trim(),
        }),
      });

      const contentType = response.headers.get("content-type") || "";
      const result = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

      if (!response.ok) {
        const errorMessage =
          typeof result === "object" && result?.detail
            ? JSON.stringify(result.detail)
            : typeof result === "string"
            ? result
            : "Analysis failed.";
        throw new Error(errorMessage);
      }

      if (result?.success === false) {
        throw new Error("Backend returned an unsuccessful response.");
      }

      setAnalysisData({
        ...result,
        ...documentInfo,
        originalText: analysisText,
      });

      setStep(2);
    } catch (error) {
      console.error("ScamShield Analysis Error:", error);
      alert(
        `Unable to analyze the input.\n\n${error.message}\n\nMake sure the ScamShield backend is running on http://127.0.0.1:8000`
      );
    } finally {
      setProcessingMessage("");
      setLoading(false);
    }
  };

  /* -------------------------------------------------------
     ANALYZE ANOTHER
  ------------------------------------------------------- */

  const handleAnalyzeAnother = () => {

    setAnalysisData(null);

    setStep(1);

  };


  return (
    <div
      className={`app ${theme}`}
    >

      <Header
        theme={theme}
        setTheme={setTheme}
      />


      {step === 1 ? (

        <StepOne
          onAnalyze={
            handleAnalyze
          }
          loading={loading}
          processingMessage={processingMessage}
        />

      ) : (

        <StepTwo
          analysisData={
            analysisData
          }
          onAnalyzeAnother={
            handleAnalyzeAnother
          }
        />

      )}

    </div>
  );
}


export default App;