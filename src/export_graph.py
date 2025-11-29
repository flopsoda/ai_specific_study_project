from dotenv import load_dotenv
load_dotenv()

from graph import build_graph

app = build_graph()

# PNG 이미지로 저장
png_data = app.get_graph().draw_mermaid_png()
with open("workflow_graph.png", "wb") as f:
    f.write(png_data)

print("✅ workflow_graph.png 저장 완료!")