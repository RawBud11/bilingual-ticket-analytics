"""Every text the report and the dashboard show, in English and Spanish.

Spanish: neutral Latin American Spanish, "tú" for the Puentara team.
Keys are the same in both languages (a test checks this). "{name}" slots
are filled by t(). Category, priority, status and channel labels match
bilingual-ticket-triage and bilingual-sla-tracker.
"""

STRINGS = {
    "en": {
        "category.account_access": "Account access",
        "category.identity_verification": "Identity verification",
        "category.card_lost_stolen": "Card lost or stolen",
        "category.transfer_failed_pending": "Failed or pending transfer",
        "category.charge_dispute": "Charge dispute",
        "category.fees": "Fees",
        "category.tax_forms": "Tax forms",
        "category.app_bug": "App bug",
        "category.general_question": "General question",
        "category.uncategorized": "No category",

        "priority.low": "Low",
        "priority.normal": "Normal",
        "priority.high": "High",
        "priority.urgent": "Urgent",

        "language.en": "English",
        "language.es": "Spanish",
        "language.mixed": "Mixed",
        "language.other": "Other",

        "channel.email": "Email",
        "channel.chat": "Chat",
        "channel.phone": "Phone",
        "channel.other": "Other",

        "age.under_1": "Under 1 business day",
        "age.1_to_3": "1-3 business days",
        "age.3_to_7": "3-7 business days",
        "age.7_plus": "7+ business days",

        "col.week": "Week of",
        "col.created": "Created",
        "col.solved": "Solved",
        "col.category": "Category",
        "col.priority": "Priority",
        "col.language": "Language",
        "col.tickets": "Tickets",
        "col.last_week": "Latest week",
        "col.prev_week": "Week before",
        "col.change": "Change",
        "col.answered": "Answered",
        "col.median_frt_h": "Median first reply (h)",
        "col.sla_known": "SLA checked",
        "col.sla_met": "SLA met",
        "col.sla_met_share": "SLA met (%)",
        "col.median_resolution_h": "Median resolution (h)",
        "col.share": "Of all tickets (%)",
        "col.age": "Age",
        "col.open": "Open",
        "col.ticket_id": "Ticket ID",
        "col.age_days": "Age (business days)",
        "col.good": "Good",
        "col.bad": "Bad",
        "col.good_share": "Good (%)",
        "col.spanish_share": "Spanish (%)",

        "table.weekly_volume": "Created vs solved per week",
        "table.top_categories": "Top categories, latest week vs the week before",
        "table.frt_by_category": "First reply and resolution by category",
        "table.frt_by_priority": "First reply by priority",
        "table.frt_by_language": "First reply by language",
        "table.backlog_by_age": "Open tickets by age",
        "table.backlog_by_category": "Open tickets by category and age",
        "table.urgent_open": "Open urgent tickets",
        "table.spanish_by_week": "Spanish share per week",
        "table.satisfaction": "Satisfaction by language",

        "kpi.tickets": "Tickets",
        "kpi.median_frt": "Median first reply",
        "kpi.sla_met": "First replies within SLA",
        "kpi.open_backlog": "Open backlog",
        "kpi.spanish_share": "Spanish share",
        "unit.hours": "{value} h",

        "dq.title": "Data quality",
        "dq.rows_read": "Rows read: {n}",
        "dq.duplicates": "Duplicate ticket IDs removed: {n}",
        "dq.bad_dates": "Rows skipped, created date not readable: {n}",
        "dq.other_dates": "First reply or solved dates ignored (not readable or before created): {n}",
        "dq.language_filled": "Blank language filled in by the detector: {n}",
        "dq.priority_raised": "Priority raised to the category minimum: {n}",
        "dq.uncategorized": "Tickets with no known category: {n}",
        "dq.rows_used": "Tickets used: {n}",
        "dq.dropped_columns": "Columns not used and dropped on load: {n}",

        "insight.spanish_slower": "Spanish tickets wait {ratio}x as long as English ones for a first reply (median {es} h vs {en} h).",
        "insight.spike": "{category} tickets jumped in the week of {week}: {count}, compared with a typical {typical} per week.",
        "insight.spanish_share_change": "Spanish tickets went from {start} of all tickets in the first {weeks} weeks to {end} in the last {weeks} weeks.",
        "insight.old_backlog": "{count} open tickets are 7 or more business days old; {top_count} of them in the {category} category.",
        "insight.low_sla": "{category} has the lowest share of first replies within SLA: {share} ({met} of {total}).",
        "insight.none": "Nothing crossed the thresholds in config.py for this data.",

        "report.title": "Support ticket report",
        "report.sample_note": "Sample data: synthetic tickets for Puentara, a fictional company. The patterns in it were planted by scripts/generate_data.py.",
        "report.source": "File: {file}",
        "report.period": "Tickets created from {start} to {end}",
        "report.as_of": "Backlog and open SLAs as of {as_of}",
        "report.kpi_heading": "Key numbers",
        "report.insights_heading": "What stands out",
        "report.tables_heading": "Tables",
        "report.method": "How it is measured: first reply and resolution are wall-clock hours from created. SLA met uses the first-reply targets (urgent 60 min, 24/7; high 4 h, normal 8 h, low 16 h in business hours Mon-Fri 08:00-18:00) and counts answered tickets plus unanswered tickets already past their target.",
        "report.no_text": "This report shows counts, times, ticket IDs and categories only. Ticket text and customer details are never included.",
        "report.no_urgent": "No open urgent tickets.",
        "report.no_satisfaction": "The export has no satisfaction column.",
        "report.wrote": "Wrote {path}",
        "report.wrote_csvs": "Wrote {count} CSV tables to {path}",

        "app.title": "Support ticket analytics",
        "app.caption": "Upload a Zendesk or Freshdesk CSV export, or look at the sample data.",
        "app.language": "Language",
        "app.upload": "Upload your CSV export",
        "app.using_sample": "Showing the sample file (synthetic data for Puentara, a fictional company).",
        "app.using_upload": "Showing your file: {file}",
        "app.date_range": "Created between",
        "app.channels": "Channels",
        "app.no_rows": "No tickets match these filters. Widen the date range or pick more channels.",
        "app.chart_hint": "Chart data comes from the same code as report.py.",

        "error.file_not_found": "File not found: {path}. Check the path, or run without a path to use data/sample_export.csv.",
        "error.missing_columns": "Could not find these columns: {columns}. Rename them in your export or add your header names to COLUMN_ALIASES in config.py.",
        "error.empty": "No ticket rows with a readable created date. Dates must look like 2026-10-26 08:00.",
        "error.bad_as_of": "AS_OF must look like 2026-10-26 08:00 (got \"{value}\"). Fix it in .env or leave it empty.",
        "error.unreadable": "Could not read the file as CSV: {detail}. Export it again as CSV (UTF-8).",
    },

    "es": {
        "category.account_access": "Acceso a la cuenta",
        "category.identity_verification": "Verificación de identidad",
        "category.card_lost_stolen": "Tarjeta perdida o robada",
        "category.transfer_failed_pending": "Transferencia fallida o pendiente",
        "category.charge_dispute": "Disputa de cargo",
        "category.fees": "Comisiones",
        "category.tax_forms": "Formularios fiscales",
        "category.app_bug": "Error en la app",
        "category.general_question": "Pregunta general",
        "category.uncategorized": "Sin categoría",

        "priority.low": "Baja",
        "priority.normal": "Media",
        "priority.high": "Alta",
        "priority.urgent": "Urgente",

        "language.en": "Inglés",
        "language.es": "Español",
        "language.mixed": "Mixto",
        "language.other": "Otro",

        "channel.email": "Correo",
        "channel.chat": "Chat en vivo",
        "channel.phone": "Teléfono",
        "channel.other": "Otro",

        "age.under_1": "Menos de 1 día hábil",
        "age.1_to_3": "1 a 3 días hábiles",
        "age.3_to_7": "3 a 7 días hábiles",
        "age.7_plus": "7 o más días hábiles",

        "col.week": "Semana del",
        "col.created": "Creados",
        "col.solved": "Resueltos",
        "col.category": "Categoría",
        "col.priority": "Prioridad",
        "col.language": "Idioma",
        "col.tickets": "Tickets",
        "col.last_week": "Última semana",
        "col.prev_week": "Semana anterior",
        "col.change": "Cambio",
        "col.answered": "Respondidos",
        "col.median_frt_h": "Mediana de primera respuesta (h)",
        "col.sla_known": "SLA revisado",
        "col.sla_met": "Cumplieron el SLA",
        "col.sla_met_share": "SLA cumplido (%)",
        "col.median_resolution_h": "Mediana de resolución (h)",
        "col.share": "Del total (%)",
        "col.age": "Antigüedad",
        "col.open": "Abiertos",
        "col.ticket_id": "ID del ticket",
        "col.age_days": "Antigüedad (días hábiles)",
        "col.good": "Buena",
        "col.bad": "Mala",
        "col.good_share": "Buenas (%)",
        "col.spanish_share": "En español (%)",

        "table.weekly_volume": "Creados y resueltos por semana",
        "table.top_categories": "Categorías principales, última semana y la anterior",
        "table.frt_by_category": "Primera respuesta y resolución por categoría",
        "table.frt_by_priority": "Primera respuesta por prioridad",
        "table.frt_by_language": "Primera respuesta por idioma",
        "table.backlog_by_age": "Tickets abiertos por antigüedad",
        "table.backlog_by_category": "Tickets abiertos por categoría y antigüedad",
        "table.urgent_open": "Tickets urgentes abiertos",
        "table.spanish_by_week": "Porcentaje en español por semana",
        "table.satisfaction": "Satisfacción por idioma",

        "kpi.tickets": "Tickets",
        "kpi.median_frt": "Mediana de primera respuesta",
        "kpi.sla_met": "Primeras respuestas dentro del SLA",
        "kpi.open_backlog": "Tickets abiertos",
        "kpi.spanish_share": "Porcentaje en español",
        "unit.hours": "{value} h",

        "dq.title": "Calidad de los datos",
        "dq.rows_read": "Filas leídas: {n}",
        "dq.duplicates": "IDs de ticket duplicados eliminados: {n}",
        "dq.bad_dates": "Filas omitidas porque no se pudo leer la fecha de creación: {n}",
        "dq.other_dates": "Fechas de primera respuesta o resolución ignoradas (no se pudieron leer o son anteriores a la creación): {n}",
        "dq.language_filled": "Idioma vacío completado por el detector: {n}",
        "dq.priority_raised": "Prioridad subida al mínimo de la categoría: {n}",
        "dq.uncategorized": "Tickets sin una categoría conocida: {n}",
        "dq.rows_used": "Tickets usados: {n}",
        "dq.dropped_columns": "Columnas que no se usan y se quitaron al cargar: {n}",

        "insight.spanish_slower": "Los tickets en español esperan {ratio} veces más que los tickets en inglés por la primera respuesta (mediana de {es} h frente a {en} h).",
        "insight.spike": "Los tickets de {category} subieron en la semana del {week}: {count}, cuando lo habitual son {typical} por semana.",
        "insight.spanish_share_change": "Los tickets en español pasaron del {start} del total en las primeras {weeks} semanas al {end} en las últimas {weeks} semanas.",
        "insight.old_backlog": "{count} tickets abiertos tienen 7 o más días hábiles de antigüedad; {top_count} de ellos son de la categoría {category}.",
        "insight.low_sla": "{category} es la categoría que menos cumple el SLA de primera respuesta: {share} ({met} de {total}).",
        "insight.none": "Nada superó los umbrales de config.py con estos datos.",

        "report.title": "Informe de tickets de soporte",
        "report.sample_note": "Datos de muestra: tickets sintéticos de Puentara, una empresa ficticia. Los patrones de estos datos se crearon a propósito con scripts/generate_data.py.",
        "report.source": "Archivo: {file}",
        "report.period": "Tickets creados del {start} al {end}",
        "report.as_of": "Tickets abiertos y SLA calculados al {as_of}",
        "report.kpi_heading": "Cifras clave",
        "report.insights_heading": "Lo que destaca",
        "report.tables_heading": "Tablas",
        "report.method": "Cómo se mide: la primera respuesta y la resolución son horas de reloj desde la creación. El SLA cumplido usa los objetivos de primera respuesta (urgente 60 min, 24/7; alta 4 h, media 8 h, baja 16 h en horario hábil de lunes a viernes de 08:00 a 18:00) y cuenta los tickets respondidos más los que siguen sin respuesta y ya pasaron su objetivo.",
        "report.no_text": "Este informe muestra solo conteos, tiempos, IDs de ticket y categorías. Nunca incluye el texto de los tickets ni datos de clientes.",
        "report.no_urgent": "No hay tickets urgentes abiertos.",
        "report.no_satisfaction": "La exportación no tiene una columna de satisfacción.",
        "report.wrote": "Listo: {path}",
        "report.wrote_csvs": "Se guardaron {count} tablas CSV en {path}",

        "app.title": "Análisis de tickets de soporte",
        "app.caption": "Sube una exportación CSV de Zendesk o Freshdesk, o mira los datos de muestra.",
        "app.language": "Idioma",
        "app.upload": "Sube tu exportación CSV",
        "app.using_sample": "Estás viendo el archivo de muestra (datos sintéticos de Puentara, una empresa ficticia).",
        "app.using_upload": "Estás viendo tu archivo: {file}",
        "app.date_range": "Creados entre",
        "app.channels": "Canales",
        "app.no_rows": "Ningún ticket coincide con estos filtros. Amplía las fechas o elige más canales.",
        "app.chart_hint": "Los gráficos salen del mismo código que report.py.",

        "error.file_not_found": "No se encontró el archivo: {path}. Revisa la ruta o ejecútalo sin ruta para usar data/sample_export.csv.",
        "error.missing_columns": "No se encontraron estas columnas: {columns}. Cámbiales el nombre en tu exportación o agrega tus encabezados a COLUMN_ALIASES en config.py.",
        "error.empty": "No hay filas de tickets con una fecha de creación válida. Las fechas deben verse así: 2026-10-26 08:00.",
        "error.bad_as_of": "AS_OF debe verse así: 2026-10-26 08:00 (llegó \"{value}\"). Corrígelo en .env o déjalo vacío.",
        "error.unreadable": "No se pudo leer el archivo como CSV: {detail}. Vuelve a exportarlo como CSV (UTF-8).",
    },
}


def t(lang, key, **values):
    """Text for `key` in `lang` ("en" or "es"), with {slots} filled in."""
    text = STRINGS.get(lang, STRINGS["en"])[key]
    return text.format(**values) if values else text


def pct(lang, share):
    """0.6 -> "60%" in English, "60 %" in Spanish (the style used in #5)."""
    if share is None:
        return "-"
    value = f"{share * 100:.0f}"
    return f"{value} %" if lang == "es" else f"{value}%"


def hours(value):
    """Minutes -> hours with one decimal, "-" when there is no value."""
    if value is None:
        return "-"
    return f"{value / 60:.1f}"
