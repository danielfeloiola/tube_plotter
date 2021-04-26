// wait for the DOM
document.addEventListener('DOMContentLoaded', () => {

    // define URL and important variables
    const url = "/";
    const form = document.querySelector('form');
    var result = document.getElementById("resultdiv");

    // add event listener
    form.addEventListener('submit', e => {

        // disable default submission
        e.preventDefault();

        // collect files
        const files = document.querySelector('[name=file]').files;
        const formData = new FormData();
        formData.append('file', files[0]);

        // send the file using a XML request
        const xhr = new XMLHttpRequest();


        // make a timer to run the function every 1000ms
        // to update the user about the progress
        var interval = setInterval(myTimer, 1000);

        // setting a different timeout
        // 15 minutes ??
        xhr.timeout = 900000;

        // on a response:
        xhr.onload = () => {

            // get the response text
            var response = xhr.responseText;
            console.log(response)


            if (response.includes("Please upload a GEFX file")) {
                // stop the counter and display error
                clearTimeout(interval);
                document.getElementById("infodiv").innerHTML = "Error: Please upload a GEFX file";
                document.getElementById("resultdiv").innerHTML = "";
            }
        };


        // send the reqeust
        xhr.open('POST', url);
        xhr.send(formData);


        // function that sends a xml http request to get the number of
        // images already processed by the backend
        function myTimer() {

            // make a request to the counter route
            const conterUrl = "/counter";
            const xhr2 = new XMLHttpRequest();

            // when we get the response
            xhr2.onload = () => {

                // get the response text
                var response = xhr2.responseText;

                if (response.includes("of")) {
                    // display progress
                    document.getElementById("infodiv").innerHTML = "Processed images: " + response.replace(/['"]+/g, '');
                    document.getElementById("resultdiv").innerHTML = "";

                } else if (response.includes("Analyzing file")) {
                    // start
                    document.getElementById("infodiv").innerHTML = "Analyzing file";
                    document.getElementById("resultdiv").innerHTML = "";

                    // // DEBUG:
                    console.log("Starting...")
                }
                else if (response.includes("Finished")) {

                    // also stop timer
                    //stopTimer()
                    clearTimeout(interval);

                    // Say Finished and show results link
                    document.getElementById("infodiv").innerHTML = "Finished";
                    document.getElementById("resultdiv").innerHTML = "<a target='_blank' href='/results'>Results Page</a>";

                }
            };

            // make the request to get the progress
            xhr2.open('GET', conterUrl);
            xhr2.send();

        }

    });

});
