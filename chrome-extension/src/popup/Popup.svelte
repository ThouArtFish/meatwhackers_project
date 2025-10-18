<script lang="ts">
  // fact checks the current page the user has open
  // sends a request to the python server
  // the python server returns the names of articles and the fact check results
  async function factCheck() {
    console.log("Fact checking the current page...");
  }
</script>

<template>
  <main>
    <h3>Fact or Fake</h3>

    <div>
      <button on:click={factCheck}>
        Fact check this page
      </button>
    </div>
  </main>
</template>

<style>
  :global(:root) {
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      Roboto,
      Oxygen,
      Ubuntu,
      Cantarell,
      'Open Sans',
      'Helvetica Neue',
      sans-serif;

    color-scheme: light dark;
    background-color: #242424;
  }

  @media (prefers-color-scheme: light) {
    :global(:root) {
      background-color: #fafafa;
    }

    a:hover {
      color: #ff3e00;
    }
  }

  :global(body) {
    min-width: 20rem;
    margin: 0;
  }

  @media (prefers-color-scheme: light) {
    :global(:root) {
      background-color: #fafafa;
    }

    a:hover {
      color: #ff3e00;
    }
  }

  :global(body) {
    min-width: 20rem;
    margin: 0;
  }

  main {
    text-align: center;
    padding: 1em;
    margin: 0 auto;
  }

  h3 {
    color: #ff3e00;
    text-transform: uppercase;
    font-size: 1.5rem;
    font-weight: 200;
    line-height: 1.2rem;
    margin: 2rem auto;
  }

  .calc {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 2rem;

    & > button {
      font-size: 1rem;
      padding: 0.5rem 1rem;
      border: 1px solid #ff3e00;
      border-radius: 0.25rem;
      background-color: transparent;
      color: #ff3e00;
      cursor: pointer;
      outline: none;

      width: 3rem;
      margin: 0 a;
    }

    & > label {
      font-size: 1.5rem;
      margin: 0 1rem;
    }
  }

  a {
    font-size: 0.5rem;
    margin: 0.5rem;
    color: #cccccc;
    text-decoration: none;
  }
</style>
