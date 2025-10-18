<script lang="ts">
  const PYTHON_SERVER_URL = "http://localhost:8000";

  let content: string | null = null;

  // fact checks the current page the user has open
  // sends a request to the python server
  // the python server returns the names of articles and the fact check results
  async function factCheck() {
    console.log("Fact checking the current page...");

    const res = await fetch(`${PYTHON_SERVER_URL}/factcheck`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url: window.location.href
      })
    })

    content = await res.text();
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