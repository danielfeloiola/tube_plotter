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

        // collect file
        const files = document.querySelector('[name=file]').files;
        const formData = new FormData();

        // get a string to use as id
        const generateRandomString = (length=6)=>Math.random().toString(20).substr(2, length)
        const randString = generateRandomString(12);

        //console.log(cookie.value);
        console.log(randString);

        // add to the form
        formData.append('file', files[0]);
        formData.append('string', randString);

        //document.getElementById("id").innerHTML = randString;
        document.getElementById("infodiv").innerHTML = "Starting...";

        // send the file using a XML request
        const xhr = new XMLHttpRequest();

        // make a timer to run the function every 2s (2000ms)
        // to update the user about the progress
        var interval = setInterval(myTimer, 5000);

        // setting a different timeout -> 30 minutes 
        xhr.timeout = 1800000;

        // on a response:
        xhr.onload = () => {

            // get the response text
            var response = xhr.responseText;

            // Checck the response and act accordingly...
            if (response.includes("Please upload a GEFX file")) {
                clearTimeout(interval);
                document.getElementById("infodiv").innerHTML = "Error: Please upload a GEFX file";
                document.getElementById("resultdiv").innerHTML = "";

            } else if (response.includes("Finished - index")) {
                clearTimeout(interval);
                document.getElementById("infodiv").innerHTML = "Finished";
                document.getElementById("resultdiv").innerHTML = "<a target='_blank' href='/results/"+ randString + "'>Results Page</a>";
                console.log("finished - index")

            } else if (response.includes("'Check filename'")) {
                clearTimeout(interval);
                document.getElementById("infodiv").innerHTML = "Check filename";
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

                console.log(response);

                if (response.includes("of")) {
                    // display progress
                    document.getElementById("infodiv").innerHTML = "Processed images: " + response.replace(/['"]+/g, '');
                    document.getElementById("resultdiv").innerHTML = "";
                } else if (response.includes("Finished - counter")) {
                    clearTimeout(interval);
                    document.getElementById("infodiv").innerHTML = "Finished";
                    document.getElementById("resultdiv").innerHTML = "<a target='_blank' href='/results/"+ randString + "'>Results Page</a>";;
                    console.log("Finished - 2")
    
                }
            };

            // make the request to get the progress
            xhr2.open('POST', conterUrl, true);

            const id = document.getElementById("id").innerHTML;
            //console.log(id);
            
            xhr2.send(randString);

        }
    });
});
