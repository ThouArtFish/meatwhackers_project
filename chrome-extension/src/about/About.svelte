<body>

    <!-- Header -->
    <header>
        <h1>Fact or Fake About Me</h1>
        <p>Analyze the credibility of articles with AI-powered insights.</p>
    </header>

    <!-- About Us Section -->
    <section id="about-us">
        <h2>Who We Are</h2>
        <p>We are a team of students dedicated to helping our generation navigate the flood of information online. Our goal is to make it easier to understand the reliability of news articles, identify trustworthy sources, and know which information is credible and which is not.</p>
        
        <h3>Why We Chose This Solution</h3>
        <p>With the rise of misinformation, we wanted a solution that could automatically analyse articles for credibility using AI. We chose a combination of natural language processing and evidence scoring because it allows precise, sentence-level evaluation of content.</p>

        <h3>How It Solves the Problem</h3>
        <p>This tool addresses the challenge of identifying reliable information by:</p>
        <ul>
            <li>Highlighting key sentences and words that contribute to credibility.</li>
            <li>Providing an overall reliability score for each article.</li>
            <li>Giving readers a quick visual indicator (badge) of trustworthiness.</li>
            <li>Enabling community feedback through upvotes, downvotes, and comments.</li>
        </ul>
    </section>

    <!-- Features Section -->
    <section id="features">
        <h2>Features</h2>
        <ul>
            <li>Automatic highlighting of key words and phrases in articles.</li>
            <li>Highlighting of sentences classified as evidence or hearsay.</li>
            <li>Reliability badges that display the credibility rating of each article.</li>
            <li>Community interaction features: upvote/downvote articles and add comments.</li>
        </ul>
    </section>

    <!-- Algorithm Section -->
    <section id="algorithm">
        <h2>How the AI Algorithm Works</h2>
        <p>Our AI evaluates articles using natural language processing and evidence scoring:</p>
        <ul>
            <li>Splits text into sentences using SpaCy.</li>
            <li>Identifies entities such as people, organizations, dates, money, and percentages.</li>
            <li>Classifies sentences into categories using a zero-shot classifier:
                <ul>
                    <li>Verifiable evidence: official reports, expert quotes, or primary sources.</li>
                    <li>Second-hand but attributed information: statements by named sources or organizations.</li>
                    <li>Anonymous or speculative information: rumors or unverified claims.</li>
                    <li>Neutral context: background information without claims.</li>
                </ul>
            </li>
            <li>Calculates subjectivity and polarity scores for tone analysis.</li>
            <li>Aggregates all metrics into a reliability score for the article.</li>
            <li>Highlights both sentences and key words contributing to the score.</li>
        </ul>
    </section>

    <section id="badges">
    <h2>Reliability Badges</h2>
    <p>Articles are assigned one of four reliability ratings, displayed as badges:</p>
    <ul>
        <li>
            <img src="../../public/icons/cap.svg" alt="CAP Badge Icon" width="24" height="24">
            CAP: Predominantly false or misleading information.
        </li>
        <li>
            <img src="../../public/icons/sus.svg" alt="SUS Badge Icon" width="24" height="24">
            SUS: Somewhat unreliable or questionable content.
        </li>
        <li>
            <img src="../../public/icons/mid.svg" alt="MID Badge Icon" width="24" height="24">
            MID: Moderately reliable, mix of verified and unverified information.
        </li>
        <li>
            <img src="../../public/icons/goated.svg" alt="GOATED Badge Icon" width="24" height="24">
            GOATED: Highly reliable, strong evidence and factual reporting.
        </li>
    </ul>
</section>
<section id="future">
    <h2>What We Would Do In the Future</h2>
    <p>We have many ideas about what would make a better solution if we had more time, but we could definitely boil it down to <b>four</b> key points:</p>
    <ol>
        <li>
            <p>We would love to improve by using a bigger and more thorough language models. We did not have a sufficiently fast computer running the model in order to have the commands execute in a suitable time-frame, so we had to size down.</p>

        </li>
        <li>
            <p>We would love to refine are model by using our upvoting and comment systems to weight our model during training for more accurate results. Due to our time-constraints, we were only able to add the influence of our community recommendations in a rudimentary manner.</p>

        </li>
        <li>
            <p>If we were given more time to attack this problem, we would have developed a login/user system for leaving comments, with functional nexted replies.</p>
        </li>
        <li>
            <p>Finally, if we were given more time we would have improved our search for related articles on our canvas. Due to the nature of a demo, we limited the amount of similar articles from other sites to 4, but we would be interested in developing an algorithm to measure similarity and more.</p>
        </li>
    </ol>

</section>
</body>
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
  section {
  width: 100%;
  max-width: 800px;
  padding: 1rem;
  margin-bottom: 2rem;
}

section h2, section h3 {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

section p, section ul, section ol {
  font-size: 1rem;
  line-height: 1.5;
}

</style>

