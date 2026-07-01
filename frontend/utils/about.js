// frontend/utils/about.js - Fixed Version
console.log("=== about.js loading ===");

document.addEventListener("DOMContentLoaded", () => {
    console.log("=== DOM Content Loaded ===");
    
    const hireBtn = document.querySelector(".hire-btn");
    const hireOptions = document.querySelector(".hire-options");
    
    if (!hireBtn || !hireOptions) {
        console.error("❌ Hire button or options not found!");
        return;
    }
    
    console.log("✅ Both elements found successfully!");

    // Toggle dropdown on Hire Me button click
    hireBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation(); // prevent closing on this click
        hireOptions.classList.toggle("show");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function(e) {
        if (
            hireOptions.classList.contains("show") && 
            !hireBtn.contains(e.target) && 
            !hireOptions.contains(e.target)
        ) {
            hireOptions.classList.remove("show");
            console.log("⬅️ Closed dropdown (clicked outside)");
        }
    });

    // Optional: close when clicking inside dropdown option
    hireOptions.addEventListener("click", function(e) {
        if (e.target.tagName === "A" || e.target.tagName === "BUTTON") {
            hireOptions.classList.remove("show");
            console.log("✅ Closed dropdown after selecting option");
        }
    });

    console.log("✅ Event listeners added successfully!");
});
