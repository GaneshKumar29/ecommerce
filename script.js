
// Automatic logout functionality
        document.addEventListener('DOMContentLoaded', function() {
            var inactivityTime =  1800000; // 30 minutes of inactivity
            var logoutTimer;

            function logoutUser() {
                // Send Ajax request to logout user
                $.ajax({
                    type: "GET",
                    url: "/logout", // URL to your Flask logout route
                    success: function (data) {
                        window.location.replace("/login"); // Redirect to login page after successful logout
                    }
                });
            }

function resetTimer() {
                clearTimeout(logoutTimer);
                logoutTimer = setTimeout(logoutUser, inactivityTime);
            }

            // Reset the timer on any user activity
            document.addEventListener('mousemove', function (e) {
                resetTimer();
            });

            resetTimer(); // Start the timer
        });


/*JS CODE FOR PRODUCTS.HTML */

function showDetails(productId,event) {
    // Toggle the visibility of the details div
    var detailsDiv = document.getElementById('details_' + productId);
    if (detailsDiv.style.display === 'none') {
        detailsDiv.style.display = 'block';
    } else {
        detailsDiv.style.display = 'none';
    }
    resetTimer()
   event.preventDefault()
}

function addToCart(productId) {
// Find the associated dropdown for the product
var dropdown = document.querySelector('select[data-product-id="' + productId + '"]');

// Get the selected quantity from the dropdown
var selectedQuantity = parseInt(dropdown.value);

// Send an AJAX request to check if the product is already in the cart
fetch('/check_cart/' + productId)
    .then(response => response.json())
    .then(data => {
        if (data.exists) {
            // Product already exists in cart, perform increase_quantity
            increaseQuantity(productId, selectedQuantity);
        } else {
            // Product not in cart, perform add_to_cart
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/add_to_cart/' + productId, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        // Item added successfully
                        alert(xhr.responseText);
                    } else {
                        // Failed to add item to cart
                        console.error('Failed to add item to cart:', xhr.responseText);
                    }
                }
            };

            // Prepare the data to be sent in the request body
            var data = JSON.stringify({
                'product_id': productId,
                'quantity': selectedQuantity
            });

            // Send the request with the data
            xhr.send(data);
           
        }
    })
    .catch(error => {
        console.error('Error checking cart:', error);
    });
    resetTimer()
}

function increaseQuantity(productId, selectedQuantity) {
// Prepare the data to send in the request
var requestData = {
    quantity: selectedQuantity
};

// Send the AJAX request to increase the quantity
$.ajax({
    url: '/increase_quantity/' + productId,
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify(requestData),
    success: function(response) {
        alert('Updated');
        // Optionally handle success response
    },
    error: function(xhr, status, error) {
        console.error('Error increasing quantity:', error);
        // Optionally display an error message to the user
    }
});
resetTimer()
}

/* JS CODE FOR CART.html  */


function removeFromCart(productId) {
    if (confirm('Are you sure you want to remove this item from your cart?')) {
        fetch('/remove_from_cart/' + productId, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to remove item');
            }
            //window.location.reload();
            // Optionally handle success response
        })
        .catch(error => {
            console.error('Error removing item:', error);
            // Optionally display an error message to the user
        });
    }
    resetTimer()  
}
