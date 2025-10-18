<script lang="ts">
  const PYTHON_SERVER_URL = "http://localhost:8000";

  type HighlightType = "person" | "organization" | "date" | "evidence";

  type Highlight = {
    text: string;
    paragraphIndex: number;
    type: HighlightType;
  }

  const highlightColors: Record<HighlightType, string> = {
    person: "rgba(255, 0, 0, 0.5)",
    organization: "rgba(0, 255, 0, 0.5)",
    date: "rgba(0, 0, 255, 0.5)",
    evidence: "rgba(255, 255, 0, 0.5)"
  }

  let content: string | null = null;

  // fact checks the current page the user has open
  // sends a request to the python server
  // the python server returns the names of articles and the fact check results
  async function factCheck() {
    console.log("Fact checking the current page...");

    // const res = await fetch(`${PYTHON_SERVER_URL}/factcheck`, {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json"
    //   },
    //   body: JSON.stringify({
    //     url: window.location.href
    //   })
    // })

    // content = await res.text();

    // highlight all paragraphs in the page of the current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    highlightParagraph([
      { text: "the", paragraphIndex: 0, type: "evidence" },
    ])
  }

  // adds all highlights to a given paragraph (all highlights belong to the same paragraph)
  // people, names, businesses, dates, evidence
  async function highlightParagraph(highlights: Highlight[]) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (highlights: Highlight[], highlightColors: Record<HighlightType, string>) => {
        console.log("Highlighting paragraph with highlights:", highlights);

        const paragraphs = document.getElementsByTagName("p");
        const paragraph = paragraphs[highlights[0].paragraphIndex];
        const elements: HTMLElement[] = []
        const splitPoints: number[] = [];
        highlights.forEach((highlight) => {
          const startIndex = paragraph.textContent!.indexOf(highlight.text);
          if (startIndex !== -1) {
            splitPoints.push(startIndex, startIndex + highlight.text.length);
          }
        });
        
        for (let i = 0; i < splitPoints.length; i += 2) {
          const start = splitPoints[i];
          const end = splitPoints[i + 1];
          const textBefore = paragraph.textContent!.substring(i === 0 ? 0 : splitPoints[i - 1], start);
          if (textBefore) {
            const textNode = document.createTextNode(textBefore);
            elements.push(textNode as unknown as HTMLElement);
          }
          const highlight = highlights.find(h => paragraph.textContent!.substring(start, end) === h.text)!;
          const span = document.createElement("span");
          span.textContent = highlight.text;
          span.style.backgroundColor = highlightColors[highlight.type];
          span.style.cursor = "pointer";
          span.onclick = () => {
            alert(`Highlight: ${highlight.text}`);
          }
          
          elements.push(span);
        }

        // Append any remaining text after the last highlight
        const lastEnd = splitPoints.length > 0 ? splitPoints[splitPoints.length - 1] : 0;
        const remainingText = paragraph.textContent!.substring(lastEnd);
        if (remainingText) {
          const textNode = document.createTextNode(remainingText);
          elements.push(textNode as unknown as HTMLElement);
        }

        paragraph.innerHTML = ""; // Clear existing content
        elements.forEach(el => paragraph.appendChild(el));
      },
      args: [highlights, highlightColors] // pass highlights as an argument
    })
  }
</script>

<img src="src/assets/logo.svg" alt="Logo" />

<button on:click={factCheck}>
  Fact check this page
</button>

{#if content}
  <div class="result">
    {@html content}
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
    margin: 0.5rem;
    color: hsl(0, 0%, 70%);
    text-decoration: none;
  }

  button {
    background-color: rgba(255, 255, 255, 0.25);
    border-radius: 999px;
    outline-width: 1px;
    outline-style: solid;
    outline-color: #ffffff;
    border-style: none;
    padding-inline: 1rem;
    padding-block: 0.5rem;
  }
</style>