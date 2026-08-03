import json
from pathlib import Path

NB_DIR = Path.home() / "GitHub/loan-portfolio-optimization/ml-lp-sim"
OUT = NB_DIR / "summaries"
OUT.mkdir(exist_ok=True)

for nb_path in sorted(NB_DIR.glob("*.ipynb")):
    nb = json.loads(nb_path.read_text())
    lines = [f"# {nb_path.stem}\n"]

    for cell in nb["cells"]:
        src = "".join(cell["source"]).strip()

        if cell["cell_type"] == "markdown" and src:
            lines.append(src + "\n")

        elif cell["cell_type"] == "code":
            for out in cell.get("outputs", []):
                text = ""
                if out.get("output_type") == "stream":
                    text = "".join(out.get("text", ""))
                elif out.get("output_type") in ("execute_result", "display_data"):
                    text = "".join(out.get("data", {}).get("text/plain", ""))
                elif out.get("output_type") == "error":
                    text = f"ERROR: {out.get('ename')}: {out.get('evalue')}"

                text = text.strip()
                if text:
                    if len(text) > 3000:
                        text = text[:3000] + "\n... [truncated]"
                    lines.append("```\n" + text + "\n```\n")

    md = "\n".join(lines)
    (OUT / f"{nb_path.stem}.md").write_text(md)
    print(f"{nb_path.stem}.md  {len(md):,} chars")