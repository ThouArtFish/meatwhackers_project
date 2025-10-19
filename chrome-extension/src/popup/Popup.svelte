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

  type VoteState = "none" | "upvote" | "downvote"

  const highlightColors: Record<HighlightType, string> = {
    person: "rgba(255, 0, 0, 0.5)",
    org: "rgba(0, 255, 0, 0.5)",
    date: "rgba(0, 0, 255, 0.5)",
    evidence: "rgba(255, 255, 0, 0.5)",
  }

  let state: FactCheckState = "ready";
  let upvoteCount: number = 0;
  let downvoteCount: number = 0;
  let showFeedback: boolean = false;
  let voteState: VoteState = "none"
  let comments: string[] = []
  let comment = ""
  let justClicked: Boolean = false;
  let mouse_pos = { x: 0, y: 0 }

  async function upvote() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (voteState === "upvote") return;
    if (voteState === "downvote") {
      await fetch(`${PYTHON_SERVER_URL}/articles/downvotes?url=${encodeURIComponent(tab.url!)}&change=-1`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
      }});

      downvoteCount -= 1;
    }

    voteState = "upvote"

    await fetch(`${PYTHON_SERVER_URL}/articles/upvotes?url=${encodeURIComponent(tab.url!)}&change=1`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });

    upvoteCount += 1;
  }

  async function downvote() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (voteState === "downvote") return;
    if (voteState === "upvote") {
      await fetch(`${PYTHON_SERVER_URL}/articles/upvotes?url=${encodeURIComponent(tab.url!)}&change=-1`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });

      upvoteCount -= 1;
    }

    voteState = "downvote"

    await fetch(`${PYTHON_SERVER_URL}/articles/downvotes?url=${encodeURIComponent(tab.url!)}&change=1`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });

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
    if (tab.url != "https://www.bbc.co.uk/news/business") {
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

      const highlightedPhrases: Highlight[] = data.highlighted_phrases as Highlight[];
      const gemeniResponse: string = data.response as string;
      const articles = data.related_articles as { title: string; link: string; }[];

      highlight(highlightedPhrases);
      displayHeaderIcons([
        { type: "subjectivity", value: data.subjectivity },
        { type: "polarity", value: data.polarity },
        { type: "evidence", value: data.evidence },
        { type: "total", value: data.total }
      ], gemeniResponse, articles);

      state = "completed";
      await tag();
  } else {
    let res;
    try {
      res = await fetch(`${PYTHON_SERVER_URL}/factcheck_headlines`, {
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

    const allData = await res.json();

    // Apply icons to all headlines
    displayHeaderIconsHeadlines(allData.map((data: any) => ([
        { type: "subjectivity", value: data.subjectivity },
        { type: "polarity", value: data.polarity },
        { type: "evidence", value: data.evidence },
        { type: "total", value: data.total }
      ])
    ));

    state = "completed";
    await tag();
  }
}

  // people, names, businesses, dates, evidence
  async function highlight(phrases: Highlight[]) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (phrases: any[], highlightColors: Record<string, string>) => {
      // small helper: collect all text nodes that are visible and not inside script/style or already highlighted
      function collectTextNodes(root: Node) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
          // ignore empty/whitespace-only text nodes
          if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
          // ignore nodes inside script, style, textarea, input or already highlighted spans
          let parent: Element | null = (node.parentElement as Element | null);
          while (parent) {
          const tag = parent.tagName && parent.tagName.toLowerCase();
          if (tag === 'script' || tag === 'style' || tag === 'textarea' || tag === 'input') {
            return NodeFilter.FILTER_REJECT;
          }
          if (parent.classList && parent.classList.contains('mw-highlight')) {
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

      // collect text nodes only inside article/main paragraphs; fallback to whole body if none found
      function collectTextNodesInArticleParagraphs() {
        const paragraphs = Array.from(document.querySelectorAll('article p, main p, [role="main"] p')) as Element[];
        if (paragraphs.length === 0) {
          return collectTextNodes(document.body);
        }
        const all: Text[] = [];
        for (const p of paragraphs) {
          all.push(...collectTextNodes(p));
        }
        return all;
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
        const textNodes = collectTextNodesInArticleParagraphs();

        for (let i = 0; i < textNodes.length; i++) {
        let node = textNodes[i];
        // keep searching within this text node while occurrences exist
        let nodeTextLower = node.nodeValue ? node.nodeValue.toLowerCase() : '';
        let idx = nodeTextLower.indexOf(searchLower);
        while (idx !== -1) {
          // if the node is already inside a highlight (defensive), skip
          if (node.parentElement && node.parentElement.closest && node.parentElement.closest('.mw-highlight')) {
          break;
          }

          // compute offsets
          const start = idx;
          const end = idx + search.length;

      // split at end first, then at start so the middle node is the match
          const after = node.splitText(end); // node now contains [..start..match]
          const matchNode = node.splitText(start); // matchNode contains only the matched text

          // prevent double-highlighting: if parent already has a mw-highlight child covering this area, skip
          if (matchNode.parentElement && matchNode.parentElement.classList && matchNode.parentElement.classList.contains('mw-highlight')) {
          node = after;
          nodeTextLower = node.nodeValue ? node.nodeValue.toLowerCase() : '';
          idx = nodeTextLower.indexOf(searchLower);
          continue;
          }

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
          span.style.display = 'inline';

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
      case rating < -0.3:
        return "cap.svg";
      case rating < 0.3:
        return "sus.svg";
      case rating < 0.42:
        return "mid.svg";
      default:
        return "goated.svg";
    }
  }

  async function displayHeaderIconsHeadlines(stats: { type: string; value: number }[][]) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    await chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (stats: { type: string; value: number }[][]) => {
        // Find all BBC business headline links
        let promoLinks = Array.from(document.querySelectorAll("a[class*='PromoLink']"));
        promoLinks = promoLinks.slice(0, 10);
        if (promoLinks.length === 0) {
          console.log("No PromoLink elements found.");
          return;
        }

        const descriptions: string[] = [
          "Emotional or factual bias in the content",
          "The sentiment expressed in the content: Negative, positive, or neutral",
          "The number of references to specific facts or sources",
          "The overall score of the content"
        ];

        // Inline version of findTierImage so it exists in the page context
        function findTierImage(rating: number) {
          switch (true) {
            case rating < -0.3:
              return "cap.svg";
            case rating < 0.3:
              return "sus.svg";
            case rating < 0.42:
              return "mid.svg";
            default:
              return "goated.svg";
          }
        }

        promoLinks.forEach((link, index) => {
          const theStats = stats[index]
          // Make a container for the icons (same look as your displayHeaderIcons)
          const tierImages = theStats.map(stat => findTierImage(stat.value));
          const imageSrcs = tierImages.map((tierImage) => chrome.runtime.getURL(`icons/${tierImage}`));

          const container = document.createElement("div");
          container.style.display = "flex";
          container.style.flexDirection = "row";
          container.style.alignItems = "left";
          container.style.justifyContent = "start";
          container.style.gap = "0.25rem";
          container.style.marginTop = "0.25rem";

          // Add 4 rows — one per metric
          imageSrcs.forEach((imageSrc, index) => {
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.alignItems = "center";
            row.style.justifyContent = "flex-start";
            row.style.gap = "0.25rem";

            const image = document.createElement("img");
            image.src = imageSrc;
            image.style.width = "1.5rem";
            image.style.height = "1.5rem";
            image.style.borderRadius = "0.25rem";

            const div = document.createElement("div");
            div.style.display = "flex";
            div.style.flexDirection = "row";
            div.style.alignItems = "center";
            div.style.justifyContent = "center";
            div.style.gap = "0.25rem";
            div.style.borderRadius = "999px";
            div.style.padding = "0.25rem";
            div.style.backgroundColor = "rgba(0, 0, 0, 0.2)";
            div.style.width = "fit-content";

            div.appendChild(image);
            row.appendChild(div);
            container.appendChild(row);
          });

          // Insert container after the headline link
          link.insertAdjacentElement("afterend", container);
          console.log("inserted icons after promo link");
        });
      },
      args: [stats]
    });
  }

  async function displayHeaderIcons(stats: { type: string; value: number }[], geminiResponse: string, articles: {title: string, link: string}[]) {
    console.log(stats)
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const tierImages = stats.map(stat => findTierImage(stat.value));
    const imageSrcs = tierImages.map((tierImage) => chrome.runtime.getURL(`icons/${tierImage}`));

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (stats: { type: string; value: number }[], imageSrcs: string[], geminiResponse: string, articles: {title: string, link: string}[]) => {
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


        let nodeMap = [];
        let mouse_pos = { x: 0, y: 0 };
        const canvas = document.createElement("canvas");
        canvas.width = 600;
        canvas.height = 400;
        canvas.style.backgroundColor = "white";
        mainHeading.insertAdjacentElement("afterend", canvas);
        canvas.addEventListener("click", (e) => {
          const rect = canvas.getBoundingClientRect();
          mouse_pos.x = e.clientX - rect.left;
          mouse_pos.y = e.clientY - rect.top;

          for (const node of nodeMap) {
            const dist = Math.hypot(mouse_pos.x - node.x, mouse_pos.y - node.y);
            if (dist <= node.r) {
              window.open(node.link, "_blank");
              break;
            }
          }
        });
        drawFrame(canvas, articles);
        function drawFrame(canvas, articles) {
          const ctx = canvas.getContext("2d");
          if (!ctx) return;

          ctx.clearRect(0, 0, canvas.width, canvas.height);
          const cx = canvas.width / 2;
          const cy = canvas.height / 2;
          const radius = 0.3 * Math.min(canvas.width, canvas.height);
          const angleStep = (2 * Math.PI) / articles.length;

          ctx.fillStyle = "#4f46e5";
          ctx.strokeStyle = "#10b981";
          ctx.lineWidth = 3;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.font = "18px sans-serif";

          // Draw center node
          ctx.beginPath();
          ctx.arc(cx, cy, 10, 0, 2 * Math.PI);
          ctx.fill();
          ctx.closePath();
          ctx.strokeText("Related Articles", cx, cy - 25);

          for (let i = 0; i < articles.length; i++) {
            const angle = i * angleStep;
            const x = cx + Math.cos(angle) * radius;
            const y = cy + Math.sin(angle) * radius;

            // Line from center to article
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(x, y);
            ctx.stroke();

            // Article circle
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, 2 * Math.PI);
            ctx.fill();
            ctx.closePath();

            // Article title
            const textOffset = 25; // push text outward a bit
            const textX = cx + Math.cos(angle) * (radius + textOffset);
            const textY = cy + Math.sin(angle) * (radius + textOffset);
            ctx.strokeText(articles[i].title, textX, textY);

            // Save node data for click detection
            nodeMap.push({ x, y, r: 10, link: articles[i].link });
          }
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

    return await res.then((injectionResults: any) => {
      for (const frameResult of injectionResults) {
        return frameResult.result as boolean;
      }

      return false;
    });
  }

  // https://www.bbc.co.uk/news/articles/c62e7xz02dpo
  function getArticleId(url: string): string | null {
    try {
      const u = new URL(url);
      const path = u.pathname;

      // common pattern: /.../articles/{articleId}
      const m = path.match(/\/articles\/([^\/?#]+)/i);
      if (m && m[1]) return m[1];

      // fallback: last non-empty path segment if it looks like an id (alphanumeric)
      const segments = path.split('/').filter(Boolean);
      if (segments.length) {
        const last = segments[segments.length - 1];
        if (/^[a-z0-9_-]+$/i.test(last)) return last;
      }

      // check common query params
      const idFromQuery = u.searchParams.get('id') || u.searchParams.get('articleId') || u.searchParams.get('guid');
      if (idFromQuery) return idFromQuery;

    } catch (e) {
      // invalid URL
    }
    return null;
  }

  async function onSubmit(e: SubmitEvent) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const res = await fetch(`${PYTHON_SERVER_URL}/articles/comments?link=${encodeURIComponent(tab.url!)}&comment=${comment}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });

    if (res.status === 200) {
      comments = [...comments, comment]
      comment = ""
    }
  }

  onMount(async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    try {
      const votes = await fetch(`${PYTHON_SERVER_URL}/votes_by_url?url=${encodeURIComponent(tab.url!)}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (votes.status === 200) {
        const json = await votes.json()
        upvoteCount = json.upvotes
        downvoteCount = json.downvotes
        showFeedback = true; 
      }
    } catch (error) {
      console.error(error)
      showFeedback = false;
    }

    try {
      const res = await fetch(`${PYTHON_SERVER_URL}/articles/comments?link=${encodeURIComponent(tab.url!)}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json"
        }
      });

      if (res.status === 200) {
        const json = await res.json()
        comments = json.comments.map((comment: any) => comment.comment_text)
        console.log(json.comments)
      }
    } catch (error) {
      console.error(error)
      showFeedback = false;
    }

    const tagged = await checkTag();
    if (tagged) {
      state = "completed";
    }
  });
</script>

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

{#if showFeedback}
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

    <form on:submit|preventDefault={onSubmit}>
      <input class="comment-input" type="text" placeholder="Add a comment..." bind:value={comment} />
    </form>

    <div class="comments">
      {#each comments as comment}
        <p>{comment}</p>
      {/each}
    </div>
  </div>
{/if}

<a href="about.html" target="_blank">Click here to learn more</a>

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
    border-radius: 0.5rem;
    border: none;
    outline-width: 1px;
    outline-style: solid;
    outline-color: #ffffff;
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }

  .full {
    opacity: 1;
  }
</style>