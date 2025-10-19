<script lang="ts">
  import Spinner from "./Spinner.svelte";
  import ThumbsUp from './ThumbsUp.svelte'
  import ThumbsDown from './ThumbsDown.svelte'
  import { onMount } from 'svelte'

  const PYTHON_SERVER_URL = "http://localhost:8000";

  const badgeColors: Record<string, string> = {
    "subjectivity": "rgba(255, 165, 0, 0.8)",
    "polarity": "rgba(0, 128, 255, 0.8)",
    "evidence": "rgba(0, 255, 0, 0.8)",
    "total": "rgba(128, 0, 255, 0.8)",
  }

  type HighlightType = "person" | "org" | "date" | "evidence";

  type Highlight = {
    text: string;
    type: HighlightType;
  }

  type FactCheckState = "ready" | "factChecking" | "completed";

  const highlightColors: Record<HighlightType, string> = {
    person: "rgba(255, 0, 0, 0.5)",
    org: "rgba(0, 255, 0, 0.5)",
    date: "rgba(0, 0, 255, 0.5)",
    evidence: "rgba(255, 255, 0, 0.5)",
  }

  let state: FactCheckState = "ready";
  let upvoteCount: number = 0;
  let downvoteCount: number = 0;

  let canvas:  HTMLCanvasElement;
  let canvasDisplay: Boolean = false;
  let justClicked: Boolean = false;
  let articleArray: any[] = [];
  let mouse_pos = {x: 0, y: 0}

  async function upvote() {
    upvoteCount += 1;
  }

  async function downvote() {
    downvoteCount += 1;
  }

  // fact checks the current page the user has open
  // sends a request to the python server
  // the python server returns the names of articles and the fact check results
  async function factCheck() {
    if (state !== "ready") return; // prevent multiple clicks
    state = "factChecking";

    console.log("Fact checking the current page...");
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    let res;
    try {
      res = await fetch(`${PYTHON_SERVER_URL}/factcheck_article?url=${encodeURIComponent(tab.url!)}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });
    } catch (error) {
      console.error("Error fetching from Python server:", error);
      state = "ready";
      return;
    }

    const data = await res.json();
    console.log(data)
    articleArray = data.related_articles

    const highlightedPhrases: Highlight[] = data.highlighted_phrases as Highlight[];
    const gemeniResponse: string = data.response as string;

    highlight(highlightedPhrases);
    displayHeaderIcons([
      { type: "subjectivity", value: data.subjectivity },
      { type: "polarity", value: data.polarity },
      { type: "evidence", value: data.evidence },
      { type: "total", value: data.total }
    ], gemeniResponse);
    state = "completed";
    await tag();
  }

  // people, names, businesses, dates, evidence
  async function highlight(phrases: Highlight[]) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (phrases: any[], highlightColors: Record<string, string>) => {
        // small helper: collect all text nodes that are visible and not inside script/style
        function collectTextNodes(root: Node) {
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
              // ignore empty/whitespace-only text nodes
              if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
              // ignore nodes inside script, style, textarea, input
              let parent = node.parentElement;
              while (parent) {
                const tag = parent.tagName && parent.tagName.toLowerCase();
                if (tag === 'script' || tag === 'style' || tag === 'textarea' || tag === 'input') {
                  return NodeFilter.FILTER_REJECT;
                }
                parent = parent.parentElement;
              }
              return NodeFilter.FILTER_ACCEPT;
            }
          });
          const nodes: Text[] = [];
          let current = walker.nextNode();
          while (current) {
            nodes.push(current as Text);
            current = walker.nextNode();
          }
          return nodes;
        }

        // ensure a single popup element exists
        function ensurePopup() {
          let existing = document.getElementById('mw-fact-popup');
          if (existing) return existing;
          const popup = document.createElement('div');
          popup.id = 'mw-fact-popup';
          popup.style.position = 'absolute';
          popup.style.zIndex = '2147483647';
          popup.style.background = 'white';
          popup.style.color = 'black';
          popup.style.padding = '0.5rem';
          popup.style.borderRadius = '0.5rem';
          popup.style.boxShadow = '0 6px 18px rgba(0,0,0,0.2)';
          popup.style.maxWidth = '320px';
          popup.style.fontSize = '0.9rem';
          popup.style.display = 'none';
          document.body.appendChild(popup);
          return popup;
        }

        function showPopup(content: string, x: number, y: number) {
          const popup = ensurePopup();
          popup.innerText = content;
          popup.style.left = x + 'px';
          // prefer above the click if there's space
          const aboveY = y - popup.offsetHeight - 12;
          if (aboveY > 0) {
            popup.style.top = aboveY + 'px';
          } else {
            popup.style.top = (y + 12) + 'px';
          }
          popup.style.display = 'block';

          // click anywhere else closes popup
          function onDocClick(e: MouseEvent) {
            const target = e.target as Node;
            if (!popup.contains(target)) {
              popup.style.display = 'none';
              document.removeEventListener('click', onDocClick);
            }
          }
          // small timeout so the same click that opened doesn't immediately close it
          setTimeout(() => document.addEventListener('click', onDocClick), 0);
        }

        // highlight a single phrase across text nodes using ranges / splitText
        function highlightPhrase(textToFind: string, type: string) {
          if (!textToFind || typeof textToFind !== 'string') return;
          const search = textToFind.trim();
          if (!search) return;
          const searchLower = search.toLowerCase();
          const textNodes = collectTextNodes(document.body);

          for (let i = 0; i < textNodes.length; i++) {
            let node = textNodes[i];
            // keep searching within this text node while occurrences exist
            let nodeTextLower = node.nodeValue ? node.nodeValue.toLowerCase() : '';
            let idx = nodeTextLower.indexOf(searchLower);
            while (idx !== -1) {
              // compute offsets
              const start = idx;
              const end = idx + search.length;

              // split at end first, then at start so the middle node is the match
              const after = node.splitText(end); // node now contains [..start..match]
              const matchNode = node.splitText(start); // matchNode contains only the matched text

              // create wrapper span
              const span = document.createElement('span');
              span.className = 'mw-highlight';
              span.dataset.mwType = type;
              span.textContent = matchNode.data;
              const color = (highlightColors && highlightColors[type]) ? highlightColors[type] : 'rgba(255,255,0,0.5)';
              span.style.backgroundColor = color;
              span.style.borderRadius = '0.2rem';
              span.style.padding = '0 0.15rem';
              span.style.cursor = 'pointer';
              span.style.transition = 'outline 0.08s ease';

              // click handler to show popup
              span.addEventListener('click', (ev: MouseEvent) => {
                ev.stopPropagation();
                const content = `${type.toUpperCase()}: ${matchNode.data}`;
                // position near click: use clientX/Y + page scroll
                const x = ev.pageX;
                const y = ev.pageY;
                showPopup(content, x, y);
              });

              // replace the text node containing match with span
              matchNode.parentNode!.replaceChild(span, matchNode);

              // continue searching in the node after the match
              node = after;
              nodeTextLower = node.nodeValue ? node.nodeValue.toLowerCase() : '';
              idx = nodeTextLower.indexOf(searchLower);
            }
          }
        }

        // iterate phrases and highlight them
        for (const p of phrases) {
          try {
            highlightPhrase(p.text, p.type);
          } catch (e) {
            console.error('Highlight error for phrase', p, e);
          }
        }

        // optional: add a small stylesheet for highlighted spans (if not already present)
        if (!document.getElementById('mw-highlight-style')) {
          const style = document.createElement('style');
          style.id = 'mw-highlight-style';
          style.textContent = `
            .mw-highlight:hover { outline: 2px solid rgba(255,255,255,0.15); }
            #mw-fact-popup { pointer-events: auto; }
          `;
          document.head.appendChild(style);
        }
      },
      args: [phrases, highlightColors] // pass highlights as an argument
    })
  }

  // returns correct icon depending on rating
  function findTierImage(rating: number) {
    switch (true) {
      case rating < 0.1:
        return "cap.svg";
      case rating < 0.3:
        return "sus.svg";
      case rating < 0.5:
        return "mid.svg";
      default:
        return "goated.svg";
    }
  }

  async function displayHeaderIcons(stats: { type: string; value: number }[], geminiResponse: string) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const tierImages = stats.map(stat => findTierImage(stat.value));
    const imageSrcs = tierImages.map((tierImage) => chrome.runtime.getURL(`icons/${tierImage}`));

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (stats: { type: string; value: number }[], imageSrcs: string[], geminiResponse: string, badgeColors: Record<string, string>) => {
        // Heading icons
        let mainHeading = document.getElementById("main-heading");
        console.log("Main heading:", mainHeading);
        if (!mainHeading) return;

        const descriptions: string[] = [
          "Emotional or factual bias in the content",
          "The sentiment expressed in the content: Negative, positive, or neutral",
          "The number of references to specific facts or sources",
          "The overall score of the content"
      ];

        const container = document.createElement("div");
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.alignItems = "left";
        container.style.justifyContent = "start";
        container.style.gap = "0.5rem";

        imageSrcs.forEach((imageSrc, index) => {
          const row = document.createElement("div");
          row.style.display = "flex";
          row.style.alignItems = "center";
          row.style.justifyContent = "flex-start";
          row.style.gap = "0.5rem";

          const description = document.createElement("span");
          description.innerText = `${stats[index].type} - ${descriptions[index]}`;
          description.style.color = "rgba(0, 0, 0)";
          description.style.fontSize = "1rem";

          const image = document.createElement("img");
          image.src = imageSrc;
          image.style.width = "2rem";
          image.style.height = "2rem";
          image.style.borderRadius = "0.25rem";

          const div = document.createElement("div");
          div.style.display = "flex";
          div.style.flexDirection = "row";
          div.style.alignItems = "center";
          div.style.justifyContent = "center";
          div.style.gap = "0.5rem";
          div.style.borderRadius = "999px";
          div.style.padding = "0.25rem";

          div.style.backgroundColor = "rgb(0, 0, 0, 0.2)";
          div.style.width = "fit-content";

          div.appendChild(image);
          row.appendChild(div);
          row.appendChild(description);
          container.appendChild(row);
        });

        mainHeading.insertAdjacentElement("afterend", container);

        // Top page summary box
        let summary = document.createElement("p");
        summary.id = "summary";
        mainHeading.insertAdjacentElement("beforebegin", summary);
        summary.innerText = geminiResponse;
      },
      args: [stats, imageSrcs, geminiResponse, badgeColors]
    })
  }

  async function tag() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: () => {
        const tag = document.createElement("div");
        tag.id = "has-been-fact-checked";
        document.body.appendChild(tag);
      }
    })
  }

  async function checkTag(): Promise<boolean> {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const res =chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: () => {
        return document.getElementById("has-been-fact-checked") !== null;
      }
    })

    return await res.then((injectionResults) => {
      for (const frameResult of injectionResults) {
        return frameResult.result as boolean;
      }

      return false;
    });
  }

  onMount(async () => {
    const tagged = await checkTag();
    if (tagged) {
      state = "completed";
    }
  });

  function quitCheck(e: KeyboardEvent) {
    if (e.key == "Escape") {
      canvasDisplay = false;
      articleArray = [];
      window.removeEventListener("keydown", quitCheck);
      window.removeEventListener("mousedown", clickCheck);
    }
  }

  function clickCheck(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();

    mouse_pos.x = e.clientX - rect.left;
    mouse_pos.y = e.clientY - rect.top;

    justClicked = true;
  }

  function drawFrame() {
    const ctx = canvas.getContext("2d");
    if (!ctx) { return }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let cx = canvas.width / 2;
    let cy = canvas.height / 2;
    let start_angle = (2 * Math.PI) / articleArray.length;
    ctx.fillStyle = "#4f46e5";
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 2;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = "8px";

    for (let i = 0; i < articleArray.length; i++) {
      let x = cx + Math.cos(start_angle * (i + 1)) * 0.3 * canvas.width
      let y = cy + Math.sin(start_angle * (i + 1)) * 0.3 * canvas.height
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(cx, cy);
      ctx.stroke();
      ctx.closePath();

      ctx.beginPath();
      ctx.arc(x, y, 10, 0, 2 * Math.PI);
      ctx.fill();
      ctx.closePath();

      ctx.strokeText(articleArray[i].title, x, y, 20)

      if (justClicked) {
        justClicked = false
        let cont = {
          l: x - 10,
          r: x + 10,
          u: y - 10,
          d: y + 10
        }
        if (mouse_pos.x > cont.l && mouse_pos.x < cont.r && mouse_pos.y > cont.u && mouse_pos.y < cont.d) {
          window.open(articleArray[i].link)
        }
      }
    }

    ctx.beginPath();
    ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
    ctx.fill();
    ctx.closePath();

    ctx.strokeText("Related Articles", cx, cy, 20)

    requestAnimationFrame(drawFrame)
  }
</script>

{#if !canvasDisplay}
  <img src="src/assets/logo.svg" alt="Logo" />
  {#if state === "factChecking"}
    <Spinner />
    <p>Fact checking in progress...</p>
  {:else if state === "completed"}
    <p>Fact check complete!</p>
  {:else}
    <button class="fact-check-button" on:click={factCheck}>
      Fact check this page
    </button>
  {/if}
  <div class="feedback-container">
    <div class="ratings-container">
      <div class="count-container">
        <button class="rating-button" on:click={upvote}><ThumbsUp /></button>
        <span class="count">{upvoteCount}</span>
      </div>
      
      <div class="count-container">
        <button class="rating-button" on:click={downvote}><ThumbsDown /></button>
        <span class="count">{downvoteCount}</span>
      </div>

    </div>

    <input class="comment-input" type="text" placeholder="Add a comment..." />
  </div>

  {#if articleArray.length != 0}
    <button class="fact-check-button" on:click={()=>{
      canvasDisplay = true;
      window.addEventListener("keydown", e => quitCheck(e))
      window.addEventListener("mousedown", e => clickCheck(e))
      requestAnimationFrame(drawFrame);
    }}>
      See visualization of related articles
    </button>
  {/if}

  <a href="about.html" target="_blank">Click here to learn more</a>
{:else}
  <canvas bind:this={canvas} id="display"></canvas>
{/if}

<style>
  * {
    color: #ffffff;
    font-family: 'Noto Serif', serif;
  }

  :global(:root) {
    background-color: #242424;
  }

  :global(body) {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: start;
    min-width: 20rem;
  }

  a {
    font-size: 0.5rem;
    margin: 0.25rem;
    color: hsl(0, 0%, 70%);
    text-decoration: none;
  }

  button.rating-button {
    transition: opacity 0.2s ease;
    background-color: transparent;
    border: none;
    padding: 0.25rem;
    opacity: 0.5;
  }

  button.rating-button:hover {
    transition: opacity 0.2s ease;
    opacity: 1.0;
    cursor: pointer;
  }

  button.fact-check-button {
    transition: background-color 0.2s ease;
    background-color: rgba(255, 255, 255, 0.25);
    border-radius: 999px;
    outline-width: 1px;
    outline-style: solid;
    outline-color: #ffffff;
    border-style: none;
    padding-inline: 1rem;
    padding-block: 0.5rem;
  }
  
  button.fact-check-button:hover {
    transition: background-color 0.2s ease;
    background-color: rgba(255, 255, 255, 0.35);
  }

  .ratings-container {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: center;
    gap: 1rem;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  .count-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.25rem;
  }

  .feedback-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 1rem;
    margin-bottom: 1rem;
    width: 100%;
  }

  .comment-input {
    margin-top: 0.5rem;
    padding: 0.5rem;
    width: 70%;
    border-radius: 0.5rem;
    border: none;
    outline-width: 1px;
    outline-style: solid;
    outline-color: #ffffff;
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }
</style>