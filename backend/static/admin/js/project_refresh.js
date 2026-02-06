// Auto-refresh the project list if any project is currently processing
(function () {
    // Check if we are on the changelist page
    if (document.getElementById('changelist-form')) {
        // We'll look for a specific indicator in the page, 
        // Or just refresh every 10 seconds if we're on this page and status is processing.
        // For simplicity, we just refresh if the URL contains the app name 
        // and we detect "Processing" in the status column.

        setInterval(function () {
            const hasProcessing = document.body.innerText.indexOf('Processing') !== -1 ||
                document.body.innerText.indexOf('Transcribing') !== -1 ||
                document.body.innerText.indexOf('Mapping') !== -1 ||
                document.body.innerText.indexOf('Generating') !== -1 ||
                document.body.innerText.indexOf('Rendering') !== -1;

            if (hasProcessing) {
                console.log("Processing detected, auto-refreshing in 10s...");
                window.location.reload();
            }
        }, 10000); // 10 seconds
    }
})();
