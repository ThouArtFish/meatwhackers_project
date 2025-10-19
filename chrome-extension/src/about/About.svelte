<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Article Reliability Checker</title>
</head>
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

</body>
</html>
