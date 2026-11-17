# Welcome to the IAI Research Pipeline

This pipeline automatically discovers, standardizes, and visualizes research published by the Institute for Artificial Intelligence.

## Interactive Graph Explorer

Click the button below to launch the explorer in Full Screen. 
* **Paper View**: Click a paper to instantly reshape the graph, showing only the papers it references, and the papers derived from it.
* **Author View**: Seamlessly switch to see the IAI co-authorship network.

<button onclick="document.getElementById('graph-frame').requestFullscreen()" style="padding: 10px 20px; background-color: #1a73e8; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; margin-bottom: 15px;">🔍 Launch Full-Screen App</button>

<iframe id="graph-frame" src="graph_app.html" width="100%" height="600px" style="border:1px solid #e8eaed; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></iframe>