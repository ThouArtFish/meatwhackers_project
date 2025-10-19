<script lang="ts">
  import Spinner from "./Spinner.svelte";
  import ThumbsUp from './ThumbsUp.svelte'
  import ThumbsDown from './ThumbsDown.svelte'
  import { onMount } from 'svelte'

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
  let upvoteCount: number = 0;
  let downvoteCount: number = 0;

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

    const highlightedSentences: Highlight[] = data.highlighted_sentences as Highlight[];
    const highlightedWords: Highlight[] = data.highlighted_words as Highlight[];
    const highlights: Highlight[] = highlightedSentences.concat(highlightedWords);
    const totalRating: number = data.total as number;
    const gemeniResponse: string = data.response as string;

    highlight(highlights);
    displayHeaderIcons(totalRating, gemeniResponse);
    state = "completed";
    await tag();
  }

  // people, names, businesses, dates, evidence
  async function highlight(highlights: Highlight[]) {
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
      func: (imageSrc: string, geminiResponse: string) => {
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
        summary.innerText = geminiResponse;
      },
      args: [imageSrc, geminiResponse]
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