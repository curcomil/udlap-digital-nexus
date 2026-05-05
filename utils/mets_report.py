from datetime import datetime


def write_report(
    path: str,
    col_name: str,
    set_spec: str,
    started_at: datetime,
    total: int,
    processed: int,
    item_errors: int,
    issues: list[dict],
) -> None:
    finished_at = datetime.now()
    elapsed = finished_at - started_at
    file_issues = [i for i in issues if i["level"] == "FILE"]
    item_issues = [i for i in issues if i["level"] == "ITEM"]

    lines = [
        "=" * 70,
        "  INFORME DE GENERACIÓN METS AIP",
        "=" * 70,
        f"  Colección   : {col_name}",
        f"  Set         : {set_spec}",
        f"  Inicio      : {started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Fin         : {finished_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Duración    : {str(elapsed).split('.')[0]}",
        f"  Items total : {total}",
        f"  Procesados  : {processed - item_errors}",
        f"  Errores item: {item_errors}",
        f"  Imgs faltantes: {len(file_issues)}",
        "",
    ]

    if not issues:
        lines += ["  ✅ Sin problemas encontrados.", ""]
    else:
        if item_issues:
            lines += [
                "─" * 70,
                f"  ERRORES CRÍTICOS DE ITEM ({len(item_issues)})",
                "  (el ZIP fue omitido completamente)",
                "─" * 70,
            ]
            for n, iss in enumerate(item_issues, 1):
                lines += [
                    "",
                    f"  [{n}] ZIP         : {iss['zip']}",
                    f"      internal_id : {iss['internal_id']}",
                    f"      Título      : {iss['titulo']}",
                    f"      Error       :",
                ]
                for detail_line in iss["detail"].splitlines():
                    lines.append(f"        {detail_line}")
            lines.append("")

        if file_issues:
            lines += [
                "─" * 70,
                f"  ARCHIVOS NO DESCARGADOS ({len(file_issues)})",
                "  (el ZIP existe pero sin estas imágenes)",
                "─" * 70,
            ]
            by_zip: dict[str, list] = {}
            for iss in file_issues:
                by_zip.setdefault(iss["zip"], []).append(iss)

            for zip_name, file_list in by_zip.items():
                lines += [
                    "",
                    f"  ZIP: {zip_name}",
                    f"  Título: {file_list[0]['titulo']}",
                    f"  internal_id: {file_list[0]['internal_id']}",
                    f"  Archivos faltantes ({len(file_list)}):",
                ]
                for iss in file_list:
                    lines.append(f"    • {iss['file_name']}")
                    lines.append(f"      URL   : {iss['url']}")
                    lines.append(f"      Causa : {iss['detail']}")
            lines.append("")

    lines += ["=" * 70, "  FIN DEL INFORME", "=" * 70]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
