article_rating = 0 // Between -1 (bullshit) and 1 (scientifically immpossible to disprove)
gemini_response = "This article is a load of shite" // Response from Gemini on Flask server

// Returns correct icon depending on rating
function findTierImage(rating) {
    rating = (rating + 1) / 2
    switch (true) {
        case rating < 0.1:
            return "cap.svg"
        case rating < 0.3:
            return "sus.svg"
        case rating < 0.5:
            return "mid.svg"
        default:
            return "goated.svg"
    }
}

function main() {
    // Heading icons
    let main_heading = document.getElementById("main-heading")
    image.src = chrome.runtime.getURL("what_path???" + findTierImage(article_rating))
    main_heading.insertAdjacentElement("afterend", image)

    // Top page summary box
    let summary = document.createElement("p")
    summary.id = "summary"
    main_heading.insertAdjacentElement("beforebegin", summary)
    summary.innerText = gemini_response
}

// Delay required cos of some bs
setTimeout(main, 3000)