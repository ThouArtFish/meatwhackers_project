<script lang="ts">
  const PYTHON_SERVER_URL = "http://localhost:8000";

  type HighlightType = "person" | "organization" | "date" | "evidence";

  type Highlight = {
    text: string;
    type: HighlightType;
  }

  type FactCheckState = "ready" | "factChecking" | "completed";

  const highlightColors: Record<HighlightType, string> = {
    person: "rgba(255, 0, 0, 0.5)",
    organization: "rgba(0, 255, 0, 0.5)",
    date: "rgba(0, 0, 255, 0.5)",
    evidence: "rgba(255, 255, 0, 0.5)"
  }

  let state: FactCheckState = "ready";

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

    const highlightedSentences: Highlight[] = data.highlighted_sentences as Highlight[];
    const totalRating: number = data.total as number;
    const gemeniResponse: string = data.response as string;

    highlightSentences(highlightedSentences);
<<<<<<< HEAD
    displayHeaderIcons(totalRating, gemeniResponse);
=======
    displayHeaderIcons(totalRating);

    state = "completed";
>>>>>>> 0ae695c8c848eb5357b61d633d59d954d81dcaac
  }

  // people, names, businesses, dates, evidence
  async function highlightSentences(highlights: Highlight[]) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (highlights: Highlight[], highlightColors: Record<HighlightType, string>) => {
        console.log("Highlighting paragraph with highlights:", highlights);

        const paragraphs = document.getElementsByTagName("p");
        for (const paragraph of paragraphs) {
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
        }
      },
      args: [highlights, highlightColors] // pass highlights as an argument
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

  async function displayHeaderIcons(rating: number, geminiResponse: string) {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    const tierImage = findTierImage(rating);
    const imageSrc = chrome.runtime.getURL(`icons/${tierImage}`);

    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (imageSrc: string) => {
        // Heading icons
        let mainHeading = document.getElementById("main-heading");
        console.log("Main heading:", mainHeading);
        if (!mainHeading) return;

        const image = document.createElement("img");
        image.src = imageSrc;
        image.style.width = "2rem";
        image.style.height = "2rem";
        image.style.borderRadius = "0.25rem";

        mainHeading.insertAdjacentElement("afterend", image);

        // Top page summary box
        let summary = document.createElement("p");
        summary.id = "summary";
        mainHeading.insertAdjacentElement("beforebegin", summary);
        summary.innerText = geminiResponse
      },
      args: [imageSrc]
    })
  }
</script>

<img src="src/assets/logo.svg" alt="Logo" />

{#if state === "factChecking"}
  <p>Fact checking in progress...</p>
{:else if state === "completed"}
  <p>Fact check complete!</p>
{:else}
  <button on:click={factCheck}>
    Fact check this page
  </button>
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
  
  button:hover {
    transition: background-color 0.2s ease;
    background-color: rgba(255, 255, 255, 0.35);
  }
</style>