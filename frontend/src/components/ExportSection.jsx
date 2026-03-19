/**
 * Export Section Component
 * PDF, Excel, and Word (.docx) export functionality with embedded chart images
 */

import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import jsPDF from "jspdf";
import { saveAs } from "file-saver";
import {
  Document,
  Packer,
  Paragraph,
  Footer,
  Table,
  TableCell,
  TableRow,
  BorderStyle,
  WidthType,
  TextRun,
  HeadingLevel,
  ImageRun,
  ShadingType,
  AlignmentType,
} from "docx";

// ─── Chart capture helpers ──────────────────────────────────────────────────

async function captureChart(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try {
    const { default: html2canvas } = await import("html2canvas");
    const canvas = await html2canvas(el, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: "#ffffff",
      logging: false,
    });
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
}

async function captureAllCharts() {
  const [acceptance, motivation, department, dependency] = await Promise.all([
    captureChart("chart-acceptance"),
    captureChart("chart-motivation"),
    captureChart("chart-department"),
    captureChart("chart-dependency"),
  ]);
  return { acceptance, motivation, department, dependency };
}

// base64 data URL → ArrayBuffer (for docx ImageRun)
function b64ToArrayBuffer(dataUrl) {
  const base64 = dataUrl.split(",")[1];
  const raw = atob(base64);
  const buf = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) buf[i] = raw.charCodeAt(i);
  return buf.buffer;
}

// ─── Component ──────────────────────────────────────────────────────────────

// ─── Timestamp helper ──────────────────────────────────────────────────────

function exportTimestamp() {
  const n = new Date();
  const pad = (v) => String(v).padStart(2, "0");
  return `${n.getFullYear()}-${pad(n.getMonth() + 1)}-${pad(n.getDate())}_${pad(n.getHours())}-${pad(n.getMinutes())}`;
}

export default function ExportSection({ data }) {
  const { t, i18n } = useTranslation();
  const [exporting, setExporting] = useState(null); // 'pdf' | 'excel' | 'word' | null
  const [modalState, setModalState] = useState(null); // { filename, format }

  const locale = i18n.language === "es" ? "es-ES" : "en-GB";
  const formatDate = () =>
    new Intl.DateTimeFormat(locale, { dateStyle: "long" }).format(new Date());

  // ── KPI calculations ────────────────────────────────────────────────────

  const calculateKPIs = () => {
    const acc = data?.acceptance_distribution ?? {};
    const total =
      (acc.very_low ?? 0) +
      (acc.low ?? 0) +
      (acc.medium ?? 0) +
      (acc.high ?? 0) +
      (acc.very_high ?? 0);
    const acceptanceRate =
      total > 0
        ? Math.round((((acc.high ?? 0) + (acc.very_high ?? 0)) / total) * 100)
        : 0;
    return {
      acceptanceRate,
      aiUsageIntensity: 42,
      employeeMotivation: 3.95,
      dependencyRiskLevel: 43,
    };
  };

  const kpis = calculateKPIs();

  const kpiRows = () => [
    {
      label: t("executive.trainingAdoption"),
      value: `${kpis.acceptanceRate}%`,
      status: t("kpi.statusMonitor"),
      color: [245, 158, 11],
    },
    {
      label: t("executive.aiUsageIntensity"),
      value: `${kpis.aiUsageIntensity}%`,
      status: t("kpi.statusMonitor"),
      color: [245, 158, 11],
    },
    {
      label: t("executive.employeeMotivation"),
      value: `${kpis.employeeMotivation}/5`,
      status: t("kpi.statusHealthy"),
      color: [34, 197, 94],
    },
    {
      label: t("executive.dependencyRiskLevel"),
      value: `${kpis.dependencyRiskLevel}%`,
      status: t("kpi.statusMonitor"),
      color: [245, 158, 11],
    },
  ];

  // ── PDF export ──────────────────────────────────────────────────────────

  const exportPDF = async () => {
    setExporting("pdf");
    let _successFile = null;
    let _pdfBlobRef = null;
    try {
      const charts = await captureAllCharts();
      const doc = new jsPDF({ unit: "mm", format: "a4" });
      const PW = doc.internal.pageSize.getWidth();
      const PH = doc.internal.pageSize.getHeight();
      const margin = 20;
      const contentW = PW - margin * 2;

      // ── Cover page ──
      doc.setFillColor(15, 52, 96);
      doc.rect(0, 0, PW, PH, "F");

      doc.setTextColor(255, 255, 255);
      doc.setFont(undefined, "bold");
      doc.setFontSize(48);
      doc.text("EvaluAI", PW / 2, 80, { align: "center" });

      doc.setFont(undefined, "normal");
      doc.setFontSize(16);
      doc.text(t("export.pdfTitle"), PW / 2, 100, { align: "center" });

      doc.setDrawColor(255, 255, 255);
      doc.setLineWidth(0.5);
      doc.line(margin, 112, PW - margin, 112);

      doc.setFontSize(12);
      doc.text(formatDate(), PW / 2, 124, { align: "center" });

      doc.setFontSize(10);
      doc.setTextColor(180, 200, 230);
      doc.text("SCALIAN Intelligence \u00A9 2026", PW / 2, PH - 20, {
        align: "center",
      });

      // ── Page decorator helper ──
      const addPageDecoration = (pageNum, totalPages) => {
        doc.setFillColor(15, 52, 96);
        doc.rect(0, 0, PW, 14, "F");
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.setFont(undefined, "bold");
        doc.text("EvaluAI Executive Report", margin, 9);
        doc.setFont(undefined, "normal");
        doc.text(formatDate(), PW - margin, 9, { align: "right" });

        doc.setFillColor(240, 244, 248);
        doc.rect(0, PH - 14, PW, 14, "F");
        doc.setTextColor(100, 116, 139);
        doc.setFontSize(8);
        doc.text(
          `${t("export.page")} ${pageNum} / ${totalPages}`,
          margin,
          PH - 6,
        );
        doc.text(
          "EvaluAI \u2013 SCALIAN Intelligence 2026",
          PW - margin,
          PH - 6,
          { align: "right" },
        );
      };

      const rows = kpiRows();
      const chartEntries = [
        { key: "acceptance", label: t("charts.acceptanceDistribution") },
        { key: "motivation", label: t("charts.motivationTrend") },
        { key: "department", label: t("charts.departmentComparison") },
        { key: "dependency", label: t("charts.dependencyRiskDistribution") },
      ];
      const hasCharts = chartEntries.some((c) => charts[c.key]);
      const totalPages = hasCharts ? 3 : 2;

      // ── Page 2: KPI snapshot ──
      doc.addPage();
      addPageDecoration(1, totalPages);

      let y = 26;
      doc.setTextColor(15, 52, 96);
      doc.setFont(undefined, "bold");
      doc.setFontSize(14);
      doc.text(t("export.executiveSnapshot"), margin, y);
      y += 8;

      doc.setFillColor(15, 52, 96);
      doc.rect(margin, y, contentW, 7, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(9);
      doc.text(t("export.kpiMetric"), margin + 2, y + 5);
      doc.text(t("export.kpiValue"), margin + contentW * 0.6 + 2, y + 5);
      doc.text(t("export.kpiStatus"), margin + contentW * 0.8 + 2, y + 5);
      y += 7;

      rows.forEach((row, i) => {
        doc.setFillColor(
          i % 2 === 0 ? 248 : 255,
          i % 2 === 0 ? 250 : 255,
          i % 2 === 0 ? 252 : 255,
        );
        doc.rect(margin, y, contentW, 8, "F");
        doc.setTextColor(30, 41, 59);
        doc.setFont(undefined, "normal");
        doc.setFontSize(9);
        doc.text(row.label, margin + 2, y + 5.5);
        doc.text(row.value, margin + contentW * 0.6 + 2, y + 5.5);

        doc.setFillColor(...row.color);
        doc.roundedRect(margin + contentW * 0.8, y + 1.5, 30, 5, 1, 1, "F");
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.text(row.status, margin + contentW * 0.8 + 15, y + 5.5, {
          align: "center",
        });
        y += 8;
      });

      y += 8;
      doc.setTextColor(15, 52, 96);
      doc.setFont(undefined, "bold");
      doc.setFontSize(12);
      doc.text(t("executive.summaryTitle"), margin, y);
      y += 7;

      doc.setFont(undefined, "normal");
      doc.setFontSize(9);
      doc.setTextColor(51, 65, 85);
      const p1 = doc.splitTextToSize(
        t("executive.summaryParagraph1"),
        contentW,
      );
      doc.text(p1, margin, y);
      y += p1.length * 4.5 + 4;
      const p2 = doc.splitTextToSize(
        t("executive.summaryParagraph2"),
        contentW,
      );
      doc.text(p2, margin, y);

      // ── Page 3: Charts ──
      if (hasCharts) {
        doc.addPage();
        addPageDecoration(2, totalPages);

        let cy = 24;
        const chartH = 55;
        const halfW = (contentW - 6) / 2;

        doc.setTextColor(15, 52, 96);
        doc.setFont(undefined, "bold");
        doc.setFontSize(13);
        doc.text(t("dashboard.analyticsTitle"), margin, cy);
        cy += 8;

        chartEntries.forEach((c, idx) => {
          if (!charts[c.key]) return;
          const col = idx % 2;
          const row = Math.floor(idx / 2);
          const x = margin + col * (halfW + 6);
          const chartY = cy + row * (chartH + 12);

          doc.setFont(undefined, "bold");
          doc.setFontSize(8);
          doc.setTextColor(71, 85, 105);
          doc.text(c.label, x, chartY);
          doc.addImage(charts[c.key], "PNG", x, chartY + 3, halfW, chartH - 3);
        });
      }

      const _pdfFile = `EvaluAI_Executive_Report_${exportTimestamp()}.pdf`;
      const pdfBlob = doc.output("blob");
      _successFile = _pdfFile;
      _pdfBlobRef = pdfBlob;
    } catch (error) {
      console.error("PDF export error:", error);
      alert(t("export.error"));
    } finally {
      setExporting(null);
      if (_successFile)
        setModalState({
          filename: _successFile,
          format: "pdf",
          blob: _pdfBlobRef,
        });
    }
  };

  // ── Excel export ────────────────────────────────────────────────────────

  const exportExcel = async () => {
    setExporting("excel");
    let _successFile = null;
    let _xlsxBlobRef = null;
    try {
      const charts = await captureAllCharts();
      const { default: ExcelJS } = await import("exceljs");
      const workbook = new ExcelJS.Workbook();
      workbook.creator = "EvaluAI";
      workbook.created = new Date();

      const navyFill = {
        type: "pattern",
        pattern: "solid",
        fgColor: { argb: "FF0F3460" },
      };
      const whiteFont = {
        name: "Calibri",
        size: 11,
        bold: true,
        color: { argb: "FFFFFFFF" },
      };
      const centerAlign = { horizontal: "center", vertical: "middle" };
      const thinBorder = {
        top: { style: "thin", color: { argb: "FFD1D5DB" } },
        bottom: { style: "thin", color: { argb: "FFD1D5DB" } },
        left: { style: "thin", color: { argb: "FFD1D5DB" } },
        right: { style: "thin", color: { argb: "FFD1D5DB" } },
      };

      function styleHeader(ws, rowNum, cols) {
        for (let c = 1; c <= cols; c++) {
          const cell = ws.getRow(rowNum).getCell(c);
          cell.fill = navyFill;
          cell.font = whiteFont;
          cell.alignment = centerAlign;
          cell.border = thinBorder;
        }
      }

      function styleDataRow(ws, rowNum, cols, isEven) {
        for (let c = 1; c <= cols; c++) {
          const cell = ws.getRow(rowNum).getCell(c);
          cell.fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: isEven ? "FFF8FAFB" : "FFFFFFFF" },
          };
          cell.border = thinBorder;
          cell.alignment = { vertical: "middle" };
        }
      }

      // ── Sheet 1: Executive Snapshot ──
      const ws1 = workbook.addWorksheet(t("export.executiveSnapshot"));
      ws1.columns = [{ width: 36 }, { width: 18 }, { width: 18 }];

      ws1.addRow([t("export.pdfTitle")]);
      ws1.getRow(1).getCell(1).font = {
        name: "Calibri",
        size: 16,
        bold: true,
        color: { argb: "FF0F3460" },
      };
      ws1.addRow([formatDate()]);
      ws1.getRow(2).getCell(1).font = {
        name: "Calibri",
        size: 11,
        color: { argb: "FF718096" },
      };
      ws1.addRow([]);

      ws1.addRow([
        t("export.kpiMetric"),
        t("export.kpiValue"),
        t("export.kpiStatus"),
      ]);
      styleHeader(ws1, 4, 3);

      kpiRows().forEach((row, i) => {
        ws1.addRow([row.label, row.value, row.status]);
        styleDataRow(ws1, 5 + i, 3, i % 2 === 0);
      });

      ws1.addRow([]);
      ws1.addRow([t("executive.summaryTitle")]);
      ws1.getRow(10).getCell(1).font = {
        name: "Calibri",
        size: 12,
        bold: true,
        color: { argb: "FF0F3460" },
      };
      ws1.addRow([t("executive.summaryParagraph1")]);
      ws1.getRow(11).getCell(1).alignment = { wrapText: true };

      // Embed chart images in Sheet 1
      const chartDefs = [
        { key: "acceptance", label: t("charts.acceptanceDistribution") },
        { key: "motivation", label: t("charts.motivationTrend") },
        { key: "department", label: t("charts.departmentComparison") },
        { key: "dependency", label: t("charts.dependencyRiskDistribution") },
      ];

      let imgRow = 14;
      for (const cd of chartDefs) {
        if (!charts[cd.key]) continue;
        ws1.addRow([]);
        ws1.addRow([cd.label]);
        ws1.getRow(imgRow).getCell(1).font = {
          bold: true,
          color: { argb: "FF0F3460" },
        };
        imgRow++;
        const imgId = workbook.addImage({
          base64: charts[cd.key].split(",")[1],
          extension: "png",
        });
        ws1.addImage(imgId, {
          tl: { col: 0, row: imgRow },
          ext: { width: 500, height: 260 },
        });
        imgRow += 17;
      }

      // ── Sheet 2: Correlation Analysis ──
      const ws2 = workbook.addWorksheet(t("export.correlationTable"));
      ws2.columns = [
        { width: 36 },
        { width: 14 },
        { width: 14 },
        { width: 22 },
      ];

      ws2.addRow([t("export.correlationTable")]);
      ws2.getRow(1).getCell(1).font = {
        name: "Calibri",
        size: 14,
        bold: true,
        color: { argb: "FF0F3460" },
      };
      ws2.addRow([]);

      ws2.addRow([
        t("correlation.metric1Label"),
        "r",
        "p-value",
        t("kpi.statusLabel"),
      ]);
      styleHeader(ws2, 3, 4);

      const corrData = [
        [
          t("executive.trainingAdoption"),
          "0.340",
          "0.085",
          t("kpi.statusMonitor"),
        ],
        [
          t("executive.aiUsageIntensity"),
          "0.280",
          "0.142",
          t("kpi.statusMonitor"),
        ],
        [t("executive.employeeMotivation"), "-0.070", "0.518", t("kpi.weak")],
        [
          t("executive.dependencyRiskLevel"),
          "0.150",
          "0.301",
          t("kpi.statusMonitor"),
        ],
        ["AI-Self-Efficacy", "0.420", "0.028", t("kpi.statusHealthy")],
      ];
      corrData.forEach((row, i) => {
        ws2.addRow(row);
        styleDataRow(ws2, 4 + i, 4, i % 2 === 0);
        const pVal = parseFloat(row[2]);
        if (!isNaN(pVal) && pVal < 0.05) {
          ws2.getRow(4 + i).getCell(3).fill = {
            type: "pattern",
            pattern: "solid",
            fgColor: { argb: "FFD1FAE5" },
          };
          ws2.getRow(4 + i).getCell(3).font = {
            color: { argb: "FF065F46" },
            bold: true,
          };
        }
      });

      // ── Sheet 3: Dataset Overview ──
      const ws3 = workbook.addWorksheet(t("dataset.overview"));
      ws3.columns = [{ width: 30 }, { width: 20 }];

      ws3.addRow([t("dataset.overview")]);
      ws3.getRow(1).getCell(1).font = {
        name: "Calibri",
        size: 14,
        bold: true,
        color: { argb: "FF0F3460" },
      };
      ws3.addRow([]);

      ws3.addRow([t("common.metric"), t("common.value")]);
      styleHeader(ws3, 3, 2);

      const overviewRows = [
        [
          t("dataset.totalEmployees"),
          data?.acceptance_distribution
            ? Object.values(data.acceptance_distribution).reduce(
                (s, v) => s + (v ?? 0),
                0,
              )
            : 0,
        ],
        [t("dataset.avgMotivation"), "3.95/5"],
        [t("dataset.avgSelfEfficacy"), "3.82/5"],
        [t("dataset.avgAIUsage"), "2.8/5"],
        [t("dataset.humanAIPreference"), t("dataset.humanAIPreferenceValue")],
        [t("dataset.primaryTool"), t("dataset.primaryToolValue")],
      ];
      overviewRows.forEach((row, i) => {
        ws3.addRow(row);
        styleDataRow(ws3, 4 + i, 2, i % 2 === 0);
      });

      const buffer = await workbook.xlsx.writeBuffer();
      const _xlsxFile = `EvaluAI_Executive_Report_${exportTimestamp()}.xlsx`;
      _xlsxBlobRef = new Blob([buffer], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      _successFile = _xlsxFile;
    } catch (error) {
      console.error("Excel export error:", error);
      alert(t("export.error"));
    } finally {
      setExporting(null);
      if (_successFile)
        setModalState({
          filename: _successFile,
          format: "excel",
          blob: _xlsxBlobRef,
        });
    }
  };

  // ── Word export ─────────────────────────────────────────────────────────

  const exportWord = async () => {
    setExporting("word");
    let _successFile = null;
    let _docxBlobRef = null;
    try {
      const charts = await captureAllCharts();
      const rows = kpiRows();

      const headerRowCells = [
        t("export.kpiMetric"),
        t("export.kpiValue"),
        t("export.kpiStatus"),
      ].map(
        (text) =>
          new TableCell({
            shading: { fill: "0F3460", type: ShadingType.SOLID },
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({ text, bold: true, color: "FFFFFF", size: 20 }),
                ],
              }),
            ],
          }),
      );

      const dataTableRows = rows.map(
        (row) =>
          new TableRow({
            children: [row.label, row.value, row.status].map(
              (text) =>
                new TableCell({
                  children: [
                    new Paragraph({
                      children: [new TextRun({ text: String(text), size: 20 })],
                    }),
                  ],
                }),
            ),
          }),
      );

      const chartBlocks = [];
      const chartDefs = [
        { key: "acceptance", label: t("charts.acceptanceDistribution") },
        { key: "motivation", label: t("charts.motivationTrend") },
        { key: "department", label: t("charts.departmentComparison") },
        { key: "dependency", label: t("charts.dependencyRiskDistribution") },
      ];
      for (const cd of chartDefs) {
        if (!charts[cd.key]) continue;
        chartBlocks.push(
          new Paragraph({
            heading: HeadingLevel.HEADING_3,
            children: [new TextRun({ text: cd.label, bold: true })],
            spacing: { before: 240, after: 120 },
          }),
        );
        chartBlocks.push(
          new Paragraph({
            children: [
              new ImageRun({
                data: b64ToArrayBuffer(charts[cd.key]),
                transformation: { width: 550, height: 280 },
              }),
            ],
            spacing: { after: 240 },
          }),
        );
      }

      const footerSignature = new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [
              new TextRun({
                text: "EvaluAI \u2013 SCALIAN Intelligence 2026",
                color: "94A3B8",
                size: 16,
              }),
            ],
          }),
        ],
      });

      const doc = new Document({
        sections: [
          {
            footers: { default: footerSignature },
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [
                  new TextRun({
                    text: "EvaluAI",
                    bold: true,
                    size: 64,
                    color: "0F3460",
                  }),
                ],
              }),
              new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 120 },
                children: [
                  new TextRun({ text: t("export.pdfTitle"), size: 32 }),
                ],
              }),
              new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 480 },
                children: [
                  new TextRun({
                    text: formatDate(),
                    size: 24,
                    color: "718096",
                  }),
                ],
              }),

              new Paragraph({
                heading: HeadingLevel.HEADING_1,
                spacing: { after: 200 },
                children: [
                  new TextRun({
                    text: t("executive.summaryTitle"),
                    bold: true,
                  }),
                ],
              }),
              new Paragraph({
                spacing: { after: 200, line: 360 },
                children: [
                  new TextRun({ text: t("executive.summaryParagraph1") }),
                ],
              }),
              new Paragraph({
                spacing: { after: 400, line: 360 },
                children: [
                  new TextRun({ text: t("executive.summaryParagraph2") }),
                ],
              }),

              new Paragraph({
                heading: HeadingLevel.HEADING_2,
                spacing: { after: 200 },
                children: [
                  new TextRun({
                    text: t("export.executiveSnapshot"),
                    bold: true,
                  }),
                ],
              }),
              new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                rows: [
                  new TableRow({ children: headerRowCells }),
                  ...dataTableRows,
                ],
              }),
              new Paragraph({ spacing: { after: 400 }, children: [] }),

              ...(chartBlocks.length > 0
                ? [
                    new Paragraph({
                      heading: HeadingLevel.HEADING_2,
                      spacing: { after: 200 },
                      children: [
                        new TextRun({
                          text: t("dashboard.analyticsTitle"),
                          bold: true,
                        }),
                      ],
                    }),
                    ...chartBlocks,
                  ]
                : []),

              new Paragraph({
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 240, after: 200 },
                children: [
                  new TextRun({
                    text: t("export.correlationTable"),
                    bold: true,
                  }),
                ],
              }),
              new Table({
                width: { size: 100, type: WidthType.PERCENTAGE },
                rows: [
                  new TableRow({
                    children: [
                      t("correlation.metric1Label"),
                      "r",
                      "p-value",
                    ].map(
                      (text) =>
                        new TableCell({
                          shading: {
                            fill: "0F3460",
                            type: ShadingType.SOLID,
                          },
                          children: [
                            new Paragraph({
                              children: [
                                new TextRun({
                                  text,
                                  bold: true,
                                  color: "FFFFFF",
                                  size: 20,
                                }),
                              ],
                            }),
                          ],
                        }),
                    ),
                  }),
                  ...[
                    [t("executive.trainingAdoption"), "0.340", "0.085"],
                    [t("executive.aiUsageIntensity"), "0.280", "0.142"],
                    [t("executive.employeeMotivation"), "-0.070", "0.518"],
                    [t("executive.dependencyRiskLevel"), "0.150", "0.301"],
                    ["AI-Self-Efficacy", "0.420", "0.028"],
                  ].map(
                    (row) =>
                      new TableRow({
                        children: row.map(
                          (text) =>
                            new TableCell({
                              children: [
                                new Paragraph({
                                  children: [new TextRun({ text, size: 20 })],
                                }),
                              ],
                            }),
                        ),
                      }),
                  ),
                ],
              }),
              new Paragraph({ spacing: { after: 400 }, children: [] }),

              new Paragraph({
                heading: HeadingLevel.HEADING_2,
                spacing: { after: 200 },
                children: [
                  new TextRun({ text: t("export.conclusion"), bold: true }),
                ],
              }),
              new Paragraph({
                spacing: { after: 200, line: 360 },
                children: [
                  new TextRun({ text: t("executive.summaryParagraph3") }),
                ],
              }),
            ],
          },
        ],
      });

      _docxBlobRef = await Packer.toBlob(doc);
      const _docxFile = `EvaluAI_Executive_Report_${exportTimestamp()}.docx`;
      _successFile = _docxFile;
    } catch (error) {
      console.error("Word export error:", error);
      alert(t("export.error"));
    } finally {
      setExporting(null);
      if (_successFile)
        setModalState({
          filename: _successFile,
          format: "word",
          blob: _docxBlobRef,
        });
    }
  };

  // ── UI ──────────────────────────────────────────────────────────────────

  return (
    <div className="mb-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 shadow-sm">
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {t("export.title")}
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {t("export.subtitle")}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={exportPDF}
          disabled={!!exporting}
          className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50 transition-colors shadow-md"
        >
          {exporting === "pdf"
            ? `\u23F3 ${t("export.exporting")}`
            : `\uD83D\uDCC4 ${t("export.pdf")}`}
        </button>

        <button
          onClick={exportExcel}
          disabled={!!exporting}
          className="px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg disabled:opacity-50 transition-colors shadow-md"
        >
          {exporting === "excel"
            ? `\u23F3 ${t("export.exporting")}`
            : `\uD83D\uDCCA ${t("export.excel")}`}
        </button>

        <button
          onClick={exportWord}
          disabled={!!exporting}
          className="px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg disabled:opacity-50 transition-colors shadow-md"
        >
          {exporting === "word"
            ? `\u23F3 ${t("export.exporting")}`
            : `\uD83D\uDCDD ${t("export.word")}`}
        </button>
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
        {t("export.chartsNote")}
      </p>

      <ExportSuccessModal
        state={modalState}
        onClose={() => setModalState(null)}
      />
    </div>
  );
}

// ─── Export Success Modal ────────────────────────────────────────────────────

function ExportSuccessModal({ state, onClose }) {
  const { t } = useTranslation();
  const progressRef = useRef(null);

  useEffect(() => {
    if (!state) return;

    // Auto-close timer
    const DURATION = 4000;
    const timer = setTimeout(onClose, DURATION);

    // Progress bar animation via direct DOM manipulation (avoids keyframe CSS)
    if (progressRef.current) {
      progressRef.current.style.width = "100%";
      progressRef.current.style.transition = `width ${DURATION}ms linear`;
      // Trigger the transition by setting to 0 in a rAF
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (progressRef.current) progressRef.current.style.width = "0%";
        });
      });
    }

    // ESC key handler
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);

    return () => {
      clearTimeout(timer);
      document.removeEventListener("keydown", handleKey);
    };
  }, [state, onClose]);

  if (!state) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="export-modal-title"
    >
      <div
        className="relative mx-4 w-full max-w-md overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl border border-gray-100 dark:border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Auto-close progress bar */}
        <div className="h-0.5 w-full bg-gray-100 dark:bg-gray-700">
          <div
            ref={progressRef}
            className="h-full bg-gray-400 dark:bg-gray-500"
            style={{ width: "100%" }}
          />
        </div>

        <div className="p-7">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700">
                <svg
                  className="h-5 w-5 text-gray-600 dark:text-gray-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.5 12.75l6 6 9-13.5"
                  />
                </svg>
              </div>
              <h3
                id="export-modal-title"
                className="text-base font-semibold text-gray-900 dark:text-white"
              >
                {t("export.successTitle")}
              </h3>
            </div>
            <button
              onClick={onClose}
              className="ml-4 flex-shrink-0 rounded-md p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
              aria-label="Close"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Message */}
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {t("export.successMessage")}
          </p>

          {/* Filename */}
          <div className="rounded-lg bg-gray-50 dark:bg-gray-700/60 border border-gray-200 dark:border-gray-600 px-4 py-3 mb-6">
            <p className="text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">
              {t("export.fileLabel")}
            </p>
            <p className="text-sm font-mono font-medium text-gray-800 dark:text-gray-100 break-all leading-relaxed">
              {state.filename}
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            {state.format === "pdf" && state.blob && (
              <button
                onClick={() => {
                  const url = URL.createObjectURL(state.blob);
                  window.open(url, "_blank");
                  setTimeout(() => URL.revokeObjectURL(url), 60_000);
                }}
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
              >
                {t("export.openPDF")}
              </button>
            )}
            {state.blob && (
              <button
                onClick={() => saveAs(state.blob, state.filename)}
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
              >
                {t("export.downloadAgain")}
              </button>
            )}
            <button
              onClick={onClose}
              className="flex-1 rounded-lg bg-gray-800 dark:bg-gray-100 px-4 py-2.5 text-sm font-medium text-white dark:text-gray-900 hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors"
            >
              {t("export.closeDialog")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
