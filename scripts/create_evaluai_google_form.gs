/**
 * EvaluAI - Google Forms generator
 *
 * What this script does:
 * 1) Creates the Google Form with questions aligned to CSV columns.
 * 2) Creates/links a Google Spreadsheet as response destination.
 * 3) Creates a tab named "csv_ready" with the exact 28 CSV columns.
 * 4) Installs an on-submit trigger that appends one normalized row per response.
 * 5) Exports csv_ready automatically to Google Drive as a .csv file.
 */

const CSV_COLUMNS = [
  "empleado_id",
  "fecha_respuesta",
  "edad",
  "genero",
  "departamento",
  "antiguedad_empresa",
  "nivel_estudios",
  "frecuencia_uso_ia",
  "herramientas_ia_utilizadas",
  "nivel_integracion_ia",
  "tipo_formacion_recibida",
  "indice_motivacion",
  "indice_desarrollo_talento",
  "indice_autoeficacia",
  "indice_experiencia_aprendizaje",
  "indice_aceptacion_ia",
  "p1_utilizo_ia_para_aprendizaje",
  "p2_ia_facilita_mi_aprendizaje",
  "p3_motivado_participar_formacion",
  "p4_interes_desarrollar_competencias",
  "p5_formacion_contribuye_crecimiento",
  "p6_mejoro_habilidades_laborales",
  "p7_confianza_afrontar_retos",
  "p8_preparado_aplicar_conocimientos",
  "p9_confio_uso_ia_aprendizaje",
  "p10_ia_util_desarrollo_profesional",
  "open_experience_ai_learning",
  "open_challenges_ai_usage",
  "open_training_needs",
];

const EXPORT_FOLDER_NAME = "EvaluAI_exports";
const EXPORT_FILE_NAME = "evaluai_responses.csv";
const OPEN_TEXT_MAX_LENGTH = 500;

const Q = {
  empleado_id: "ID de empleado",
  edad: "Edad",
  genero: "Genero",
  departamento: "Departamento",
  antiguedad_empresa: "Antiguedad en la empresa",
  nivel_estudios: "Nivel de estudios",
  frecuencia_uso_ia: "Frecuencia de uso de IA",
  herramientas_ia_utilizadas: "Herramientas IA utilizadas",
  nivel_integracion_ia: "Nivel de integracion de IA en tu aprendizaje",
  tipo_formacion_recibida: "Tipo de formacion recibida",
  indice_motivacion: "Indice de motivacion",
  indice_desarrollo_talento: "Indice de desarrollo de talento",
  indice_autoeficacia: "Indice de autoeficacia",
  indice_experiencia_aprendizaje: "Indice de experiencia de aprendizaje",
  indice_aceptacion_ia: "Indice de aceptacion de IA",
  p1_utilizo_ia_para_aprendizaje: "P1. Utilizo IA para aprendizaje",
  p2_ia_facilita_mi_aprendizaje: "P2. La IA facilita mi aprendizaje",
  p3_motivado_participar_formacion:
    "P3. Me siento motivado/a para participar en formacion",
  p4_interes_desarrollar_competencias:
    "P4. Tengo interes en desarrollar competencias",
  p5_formacion_contribuye_crecimiento:
    "P5. La formacion contribuye a mi crecimiento",
  p6_mejoro_habilidades_laborales:
    "P6. La formacion mejora mis habilidades laborales",
  p7_confianza_afrontar_retos: "P7. Tengo confianza para afrontar retos",
  p8_preparado_aplicar_conocimientos:
    "P8. Me siento preparado/a para aplicar conocimientos",
  p9_confio_uso_ia_aprendizaje: "P9. Confio en el uso de IA para aprender",
  p10_ia_util_desarrollo_profesional:
    "P10. La IA es util para mi desarrollo profesional",
  open_experience_ai_learning: "Comentarios sobre tu experiencia con IA",
  open_challenges_ai_usage: "Principales desafios al usar IA",
  open_training_needs: "Sugerencias de mejora",
};

/**
 * Run this function once to create everything.
 */
function createEvaluAIForm() {
  const form = FormApp.create("EvaluAI - Encuesta sobre formacion y uso de IA");
  form.setDescription(
    [
      "Objetivo: recoger informacion sobre uso de IA y experiencia de formacion.",
      "Nota: la fecha de respuesta se toma automaticamente del timestamp de Google Forms.",
    ].join("\n")
  );
  form.setProgressBar(true);

  addProfileSection_(form);
  addUsageSection_(form);
  addIndicesSection_(form);
  addLikertSection_(form);
  addOpenSection_(form);

  const spreadsheet = SpreadsheetApp.create(
    "EvaluAI - Respuestas Formulario IA"
  );
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());
  ensureCsvReadySheet_(spreadsheet);

  const props = PropertiesService.getScriptProperties();
  props.setProperty("EVALUAI_FORM_ID", form.getId());
  props.setProperty("EVALUAI_SPREADSHEET_ID", spreadsheet.getId());
  props.setProperty("EVALUAI_CSV_SHEET_NAME", "csv_ready");

  installSubmitTrigger_(form);
  const exportFile = exportCsvReadyToDrive_(spreadsheet, "csv_ready");

  Logger.log("Form edit URL: " + form.getEditUrl());
  Logger.log("Form public URL: " + form.getPublishedUrl());
  Logger.log("Spreadsheet URL: " + spreadsheet.getUrl());
  Logger.log("CSV export URL: " + exportFile.getUrl());
}

function onEvaluaiFormSubmit(e) {
  const props = PropertiesService.getScriptProperties();
  const spreadsheetId = props.getProperty("EVALUAI_SPREADSHEET_ID");
  const csvSheetName = props.getProperty("EVALUAI_CSV_SHEET_NAME") || "csv_ready";

  if (!spreadsheetId) {
    throw new Error(
      "Missing EVALUAI_SPREADSHEET_ID in Script Properties. Run createEvaluAIForm() first."
    );
  }

  const ss = SpreadsheetApp.openById(spreadsheetId);
  const csvSheet = ss.getSheetByName(csvSheetName) || ensureCsvReadySheet_(ss);
  const row = buildCsvRow_(e.response);
  csvSheet.appendRow(row);
  exportCsvReadyToDrive_(ss, csvSheetName);
}

/**
 * Manual utility: force export current csv_ready content to Drive.
 * Useful if you already had the form created before adding this feature.
 */
function exportCsvReadyNow() {
  const props = PropertiesService.getScriptProperties();
  const spreadsheetId = props.getProperty("EVALUAI_SPREADSHEET_ID");
  const csvSheetName = props.getProperty("EVALUAI_CSV_SHEET_NAME") || "csv_ready";
  if (!spreadsheetId) {
    throw new Error(
      "Missing EVALUAI_SPREADSHEET_ID in Script Properties. Run createEvaluAIForm() first."
    );
  }
  const ss = SpreadsheetApp.openById(spreadsheetId);
  const file = exportCsvReadyToDrive_(ss, csvSheetName);
  Logger.log("CSV export URL: " + file.getUrl());
}

function buildCsvRow_(formResponse) {
  const answers = {};
  formResponse.getItemResponses().forEach((ir) => {
    const title = ir.getItem().getTitle();
    const response = ir.getResponse();
    answers[title] = Array.isArray(response) ? response.join(", ") : response;
  });

  const timestamp = Utilities.formatDate(
    formResponse.getTimestamp(),
    Session.getScriptTimeZone(),
    "yyyy-MM-dd HH:mm:ss"
  );
  const openExperienceText = asBoundedText_(
    answers[Q.open_experience_ai_learning],
    OPEN_TEXT_MAX_LENGTH
  );
  const openChallengesText = asBoundedText_(
    answers[Q.open_challenges_ai_usage],
    OPEN_TEXT_MAX_LENGTH
  );
  const openTrainingNeedsText = asBoundedText_(
    answers[Q.open_training_needs],
    OPEN_TEXT_MAX_LENGTH
  );

  return [
    asText_(answers[Q.empleado_id]),
    timestamp,
    asInt_(answers[Q.edad]),
    asText_(answers[Q.genero]),
    asText_(answers[Q.departamento]),
    asText_(answers[Q.antiguedad_empresa]),
    asText_(answers[Q.nivel_estudios]),
    asInt_(answers[Q.frecuencia_uso_ia]),
    asText_(answers[Q.herramientas_ia_utilizadas]),
    asInt_(answers[Q.nivel_integracion_ia]),
    asText_(answers[Q.tipo_formacion_recibida]),
    asFloat_(answers[Q.indice_motivacion]),
    asFloat_(answers[Q.indice_desarrollo_talento]),
    asFloat_(answers[Q.indice_autoeficacia]),
    asFloat_(answers[Q.indice_experiencia_aprendizaje]),
    asFloat_(answers[Q.indice_aceptacion_ia]),
    asInt_(answers[Q.p1_utilizo_ia_para_aprendizaje]),
    asInt_(answers[Q.p2_ia_facilita_mi_aprendizaje]),
    asInt_(answers[Q.p3_motivado_participar_formacion]),
    asInt_(answers[Q.p4_interes_desarrollar_competencias]),
    asInt_(answers[Q.p5_formacion_contribuye_crecimiento]),
    asInt_(answers[Q.p6_mejoro_habilidades_laborales]),
    asInt_(answers[Q.p7_confianza_afrontar_retos]),
    asInt_(answers[Q.p8_preparado_aplicar_conocimientos]),
    asInt_(answers[Q.p9_confio_uso_ia_aprendizaje]),
    asInt_(answers[Q.p10_ia_util_desarrollo_profesional]),
    openExperienceText,
    openChallengesText,
    openTrainingNeedsText,
  ];
}

function addProfileSection_(form) {
  form.addSectionHeaderItem().setTitle("Perfil del empleado");

  const idValidation = FormApp.createTextValidation()
    .requireTextMatchesPattern("^EMP_[0-9]{4}$")
    .setHelpText("Formato esperado: EMP_0001")
    .build();

  form
    .addTextItem()
    .setTitle(Q.empleado_id)
    .setRequired(true)
    .setValidation(idValidation)
    .setHelpText("Ejemplo: EMP_1023");

  const ageValidation = FormApp.createTextValidation()
    .requireNumberBetween(22, 55)
    .setHelpText("Introduce una edad entre 22 y 55")
    .build();

  form
    .addTextItem()
    .setTitle(Q.edad)
    .setRequired(true)
    .setValidation(ageValidation);

  form
    .addMultipleChoiceItem()
    .setTitle(Q.genero)
    .setChoiceValues(["Hombre", "Mujer", "Prefiero no decir"])
    .setRequired(true);

  form
    .addMultipleChoiceItem()
    .setTitle(Q.departamento)
    .setChoiceValues([
      "Finanzas",
      "Marketing",
      "Operaciones",
      "Producto",
      "RRHH",
      "Tecnologia",
      "Ventas",
    ])
    .setRequired(true);

  form
    .addMultipleChoiceItem()
    .setTitle(Q.antiguedad_empresa)
    .setChoiceValues([
      "Menos de 1 ano",
      "1-3 anos",
      "3-5 anos",
      "5-10 anos",
      "Mas de 10 anos",
    ])
    .setRequired(true);

  form
    .addMultipleChoiceItem()
    .setTitle(Q.nivel_estudios)
    .setChoiceValues([
      "FP Superior",
      "Grado/Licenciatura",
      "Master",
      "Doctorado",
      "Otro",
    ])
    .setRequired(true);
}

function addUsageSection_(form) {
  form.addSectionHeaderItem().setTitle("Uso de IA y formacion");

  form
    .addScaleItem()
    .setTitle(Q.frecuencia_uso_ia)
    .setBounds(1, 5)
    .setLabels("Nunca", "Siempre")
    .setRequired(true);

  form
    .addCheckboxItem()
    .setTitle(Q.herramientas_ia_utilizadas)
    .setChoiceValues([
      "ChatGPT/Claude",
      "Copilot/GitHub Copilot",
      "Asistentes de codigo",
      "Plataformas LMS con IA",
      "Otras herramientas",
      "Ninguna",
    ])
    .setRequired(true);

  form
    .addScaleItem()
    .setTitle(Q.nivel_integracion_ia)
    .setBounds(1, 5)
    .setLabels("Muy baja", "Muy alta")
    .setRequired(true);

  form
    .addCheckboxItem()
    .setTitle(Q.tipo_formacion_recibida)
    .setChoiceValues([
      "Udemy",
      "Formacion interna",
      "Formacion tecnica",
      "Soft skills",
      "Ninguna reciente",
    ])
    .setRequired(true);
}

function addIndicesSection_(form) {
  form.addSectionHeaderItem().setTitle("Indices globales (1-7)");

  addNumericTextItem_(form, Q.indice_motivacion, 1, 7);
  addNumericTextItem_(form, Q.indice_desarrollo_talento, 1, 7);
  addNumericTextItem_(form, Q.indice_autoeficacia, 1, 7);
  addNumericTextItem_(form, Q.indice_experiencia_aprendizaje, 1, 7);
  addNumericTextItem_(form, Q.indice_aceptacion_ia, 1, 7);
}

function addLikertSection_(form) {
  form
    .addSectionHeaderItem()
    .setTitle("Bloque Likert (1 = en desacuerdo, 7 = muy de acuerdo)");

  addLikertScaleItem_(form, Q.p1_utilizo_ia_para_aprendizaje);
  addLikertScaleItem_(form, Q.p2_ia_facilita_mi_aprendizaje);
  addLikertScaleItem_(form, Q.p3_motivado_participar_formacion);
  addLikertScaleItem_(form, Q.p4_interes_desarrollar_competencias);
  addLikertScaleItem_(form, Q.p5_formacion_contribuye_crecimiento);
  addLikertScaleItem_(form, Q.p6_mejoro_habilidades_laborales);
  addLikertScaleItem_(form, Q.p7_confianza_afrontar_retos);
  addLikertScaleItem_(form, Q.p8_preparado_aplicar_conocimientos);
  addLikertScaleItem_(form, Q.p9_confio_uso_ia_aprendizaje);
  addLikertScaleItem_(form, Q.p10_ia_util_desarrollo_profesional);
}

function addOpenSection_(form) {
  form.addSectionHeaderItem().setTitle("Feedback cualitativo");

  addOpenTextItem_(form, Q.open_experience_ai_learning, true);
  addOpenTextItem_(form, Q.open_challenges_ai_usage, true);
  addOpenTextItem_(form, Q.open_training_needs, false);
}

function addOpenTextItem_(form, title, required) {
  const validation = FormApp.createTextValidation()
    .requireTextLengthLessThanOrEqualTo(OPEN_TEXT_MAX_LENGTH)
    .setHelpText(`Maximo ${OPEN_TEXT_MAX_LENGTH} caracteres`)
    .build();

  form
    .addParagraphTextItem()
    .setTitle(title)
    .setHelpText(`Maximo ${OPEN_TEXT_MAX_LENGTH} caracteres`)
    .setValidation(validation)
    .setRequired(required);
}

function addNumericTextItem_(form, title, min, max) {
  const validation = FormApp.createTextValidation()
    .requireNumberBetween(min, max)
    .setHelpText(`Introduce un numero entre ${min} y ${max}`)
    .build();

  form
    .addTextItem()
    .setTitle(title)
    .setValidation(validation)
    .setRequired(true);
}

function addLikertScaleItem_(form, title) {
  form
    .addScaleItem()
    .setTitle(title)
    .setBounds(1, 7)
    .setLabels("Muy en desacuerdo", "Muy de acuerdo")
    .setRequired(true);
}

function ensureCsvReadySheet_(spreadsheet) {
  let sheet = spreadsheet.getSheetByName("csv_ready");
  if (!sheet) {
    sheet = spreadsheet.insertSheet("csv_ready");
  }
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, CSV_COLUMNS.length).setValues([CSV_COLUMNS]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function exportCsvReadyToDrive_(spreadsheet, csvSheetName) {
  const sheet = spreadsheet.getSheetByName(csvSheetName);
  if (!sheet) {
    throw new Error(`Sheet not found: ${csvSheetName}`);
  }

  const values = sheet.getDataRange().getValues();
  const csvContent = toCsvContent_(values);
  const folder = getOrCreateExportFolder_();
  const props = PropertiesService.getScriptProperties();

  let file = null;
  const existingFileId = props.getProperty("EVALUAI_EXPORT_FILE_ID");
  if (existingFileId) {
    try {
      file = DriveApp.getFileById(existingFileId);
    } catch (err) {
      file = null;
    }
  }

  if (!file) {
    const filesByName = folder.getFilesByName(EXPORT_FILE_NAME);
    if (filesByName.hasNext()) {
      file = filesByName.next();
    }
  }

  if (file) {
    file.setContent(csvContent);
  } else {
    file = folder.createFile(EXPORT_FILE_NAME, csvContent, MimeType.CSV);
  }

  props.setProperty("EVALUAI_EXPORT_FILE_ID", file.getId());
  return file;
}

function getOrCreateExportFolder_() {
  const props = PropertiesService.getScriptProperties();
  const existingFolderId = props.getProperty("EVALUAI_EXPORT_FOLDER_ID");
  if (existingFolderId) {
    try {
      return DriveApp.getFolderById(existingFolderId);
    } catch (err) {
      // Continue and recreate if id is invalid or folder was removed.
    }
  }

  const folders = DriveApp.getFoldersByName(EXPORT_FOLDER_NAME);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(EXPORT_FOLDER_NAME);
  props.setProperty("EVALUAI_EXPORT_FOLDER_ID", folder.getId());
  return folder;
}

function toCsvContent_(values) {
  return values
    .map((row) => row.map((cell) => escapeCsvCell_(cell)).join(","))
    .join("\n");
}

function escapeCsvCell_(value) {
  const text = value == null ? "" : String(value);
  // Prevent CSV formula injection: prefix values starting with a formula
  // character with a single quote so spreadsheet applications (Excel, Google
  // Sheets, LibreOffice) treat them as plain text rather than formulas.
  const needsFormulaPrefix = /^[=+\-@]/.test(text);
  const escapedText = text.replace(/"/g, "\"\"");
  const safe = needsFormulaPrefix ? `'${escapedText}` : escapedText;
  if (
    // Quote cells that were prefixed to neutralize formula injection, as well
    // as cells containing characters that require quoting under RFC 4180.
    needsFormulaPrefix ||
    text.indexOf(",") !== -1 ||
    text.indexOf("\"") !== -1 ||
    text.indexOf("\n") !== -1 ||
    text.indexOf("\r") !== -1
  ) {
    return `"${safe}"`;
  }
  return safe;
}

function installSubmitTrigger_(form) {
  ScriptApp.getProjectTriggers()
    .filter((t) => t.getHandlerFunction() === "onEvaluaiFormSubmit")
    .forEach((t) => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger("onEvaluaiFormSubmit")
    .forForm(form)
    .onFormSubmit()
    .create();
}

function asText_(value) {
  return value == null ? "" : String(value).trim();
}

function asBoundedText_(value, maxLength) {
  const text = asText_(value);
  if (!maxLength || maxLength < 1) return text;
  return text.slice(0, maxLength);
}

function asInt_(value) {
  if (value == null || value === "") return "";
  const n = Number(String(value).replace(",", "."));
  return Number.isFinite(n) ? Math.round(n) : "";
}

function asFloat_(value) {
  if (value == null || value === "") return "";
  const n = Number(String(value).replace(",", "."));
  return Number.isFinite(n) ? n : "";
}
