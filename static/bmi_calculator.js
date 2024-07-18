document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const heightInput = document.querySelector("input[name='height']");
    const weightInput = document.querySelector("input[name='weight']");
    const bmiInput = document.querySelector("input[name='bmi']");

    function calculateBMI(height, weight) {
        // Convert height from cm to meters
        const heightInMeters = height / 100;
        return weight / (heightInMeters * heightInMeters);
    }

    function updateBMI() {
        const height = parseFloat(heightInput.value);
        const weight = parseFloat(weightInput.value);

        if (!isNaN(height) && !isNaN(weight) && height > 0 && weight > 0) {
            const bmi = calculateBMI(height, weight);
            bmiInput.value = bmi.toFixed(2);
        } else {
            bmiInput.value = '';
        }
    }

    heightInput.addEventListener("input", updateBMI);
    weightInput.addEventListener("input", updateBMI);

    form.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission
        // You can add any additional form submission logic here
    });
});
