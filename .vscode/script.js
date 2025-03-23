document.addEventListener("DOMContentLoaded", function () { 
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const API_URL = "http://127.0.0.1:8002"; // Adjust according to your backend

    console.log("Login button clicked! Sending request...");
    async function fetchToken(email, password) {
        try {
            const response = await fetch(`${API_URL}/token`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }) // Send as JSON
            });
    
            if (!response.ok) throw new Error("Failed to get token");
    
            const data = await response.json();
            console.log("Token Response:", data);
            return data.access_token;
        } catch (error) {
            console.error("Token fetch error:", error);
        }
    }
    if (loginForm) {
        loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const email = document.getElementById("loginEmail").value;
        const password = document.getElementById("loginPassword").value;
    
        try {
            // First login to get user info
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
    
            const data = await response.json();
            console.log("Login Response:", data);
    
            if (response.ok && data.message.trim().toLowerCase() === "login successful") {
                // Then get the token
                const token = await fetchToken(email, password);
                console.log("Token received:", token);
                
                if (token) {
                    localStorage.setItem("token", token);
                    console.log("Token stored in localStorage");
                    alert("Login successful!");
                    if (email === "admin@event.com") {
                        window.location.href = "manage.html"; // Redirect to Admin Page
                    } else {
                        window.location.href = "booking.html"; // Redirect to User Booking Page
                    }
                   // window.location.href = "manage.html";
                } else {
                    alert("Login successful but couldn't get authentication token");
                }
                
            } else {
                alert("Login failed: " + data.message);
            }
        } catch (error) {
            console.error("Login Error:", error);
            alert("An error occurred during login.");
        }
    });
}
    // Register
    if (registerForm) {
        registerForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const username = document.getElementById("registerUsername").value;
            const email = document.getElementById("registerEmail").value;
            const password = document.getElementById("registerPassword").value;

            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, email, password }),
                });

                const data = await response.json();
                if (response.ok) {
                    alert("Registration successful! You can now log in.");
                    window.location.href = "login.html";
                } else {
                    alert(data.detail);
                }
            } catch (error) {
                console.error("Registration Error:", error);
                alert("An error occurred during registration.");
            }
        });
    }

    // Logout Function
    function logout() {
        localStorage.removeItem("token");
        alert("You have been logged out.");
        window.location.href = "login.html";
    }

    // Attach logout to a button if exists
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }
// Fetch and Display Events with Authentication
async function fetchEvents() {
    try {
        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please log in first!");
            window.location.href = "login.html";
            return;
        }

        const response = await fetch("http://127.0.0.1:8000/events", {
            headers: { Authorization: `Bearer ${token}` }, // Attach JWT Token
        });

        if (!response.ok) throw new Error("Failed to fetch events");

        const data = await response.json();
        const eventsList = document.getElementById("events-list");
        eventsList.innerHTML = "";

        // For each event in the list, fetch the full event details
        const fetchPromises = data.events.map(eventSummary => 
            fetch(`http://127.0.0.1:8000/events/${eventSummary._id}`, {
                headers: { Authorization: `Bearer ${token}` },
            }).then(res => res.json())
        );

        // Wait for all individual event fetch operations to complete
        const fullEvents = await Promise.all(fetchPromises);

        // Now render each event with complete information
        fullEvents.forEach((event) => {
            const eventCard = document.createElement("div");
            eventCard.classList.add("event-card");
            eventCard.innerHTML = `
                <div>
                    <h3>${event.name}</h3>
                    <p>${event.description || "No description available"}</p>
                    <p><b>Location:</b> ${event.location || "No location specified"}</p>
                    <p><b>Date:</b> ${event.date || "Date TBA"}</p>
                    <p><b>Tickets Available:</b> ${event.tickets_available}</p>
                    <p><b>Event ID:</b> ${event._id}</p>
                </div>
                <button class="btn btn-book" data-id="${event._id}">SELECT</button>
            `;
            
            eventsList.appendChild(eventCard);
        });

        // Event booking handlers
        document.querySelectorAll(".btn-book").forEach((button) => {
            button.addEventListener("click", function () {
                const eventId = this.getAttribute("data-id");
                document.getElementById("event_id").value = eventId;
            });
        });

        // Delete button handlers (if applicable)
        document.querySelectorAll(".delete-btn").forEach((button) => {
            button.addEventListener("click", async function () {
                const eventId = this.getAttribute("data-id");
                try {
                    const response = await fetch(`http://127.0.0.1:8000/events/${eventId}`, {
                        method: "DELETE",
                        headers: { Authorization: `Bearer ${token}` },
                    });
                    
                    if (!response.ok) throw new Error("Failed to delete event");
                    alert("Event deleted successfully!");
                    fetchEvents();
                } catch (error) {
                    console.error("Error deleting event:", error);
                    alert("Failed to delete event.");
                }
            });
        });
    } catch (error) {
        console.error("Error fetching events:", error);
        alert("Failed to load events.");
    }
}
// Handle Booking Form Submission
const bookingForm = document.getElementById("booking-form");
if (bookingForm) {
    bookingForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        
        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please log in first!");
            window.location.href = "login.html";
            return;
        }
        
        const eventId = document.getElementById("event_id").value;
        const tickets = parseInt(document.getElementById("tickets").value);
        
        if (!eventId || isNaN(tickets) || tickets <= 0) {
            alert("Please fill in all fields correctly");
            return;
        }
        
        const bookingData = {
            event_id: eventId,
            tickets: tickets
        };

        try {
            const response = await fetch("http://127.0.0.1:5000/bookings", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` // Send token
                },
                body: JSON.stringify(bookingData)
            });

            const result = await response.json();
            
            if (response.ok) {
                alert(result.message || "Booking successful!");
                fetchEvents(); // Refresh events to show updated ticket counts
                bookingForm.reset();
            } else {
                alert(result.error || "Booking failed!");
            }
        } catch (error) {
            console.error("Error booking tickets:", error);
            alert("Failed to connect to booking service. Please try again later.");
        }
    });
}


    // Call fetchEvents if on the events page
    if (document.getElementById("events-list")) {
        fetchEvents();
    }
    async function testToken() {
        const token = localStorage.getItem("token");
        console.log("Retrieved token:", token);
        
        if (!token) {
            console.log("No token found in localStorage");
            return false;
        }
        
        try {
            const response = await fetch(`${API_URL}/usersme`, {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            
            console.log("Auth test status:", response.status);
            
            const data = await response.json();
            console.log("Auth test response:", data);
            
            return response.ok;
        } catch (error) {
            console.error("Token test error:", error);
            return false;
        }
    }
    document.addEventListener("DOMContentLoaded", function() {
        const testTokenBtn = document.getElementById("test-token-btn");
        const testResult = document.getElementById("test-result");
        
        if (testTokenBtn) {
            testTokenBtn.addEventListener("click", async function() {
                testResult.textContent = "Testing...";
                
                const isValid = await testToken();
                
                if (isValid) {
                    testResult.textContent = "✓ Token is valid";
                    testResult.style.color = "green";
                } else {
                    testResult.textContent = "✗ Token is invalid";
                    testResult.style.color = "red";
                }
            });
        }
    });
});
