/**
 * Greeni5 - Admin Management Script
 */

function initAdminIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

if (document.readyState === "complete" || document.readyState === "interactive") {
  initAdminIcons();
} else {
  document.addEventListener("DOMContentLoaded", initAdminIcons);
}
window.addEventListener("load", initAdminIcons);

document.addEventListener("DOMContentLoaded", () => {
  initAdminIcons();

  // Auto-submit status change on select change
  document.querySelectorAll(".status-select").forEach(select => {
    select.addEventListener("change", (e) => {
      const form = select.closest("form");
      if (form) {
        form.submit();
      }
    });
  });

  // Confirm delete prompts
  document.querySelectorAll(".confirm-delete").forEach(btn => {
    btn.addEventListener("click", (e) => {
      if (!confirm("Are you sure you want to permanently delete this item? This action cannot be undone.")) {
        e.preventDefault();
      }
    });
  });

  // Multiple Image File Preview
  const imageFileInput = document.getElementById("plant-image-files");
  const previewContainer = document.getElementById("image-preview-box");
  if (imageFileInput && previewContainer) {
    imageFileInput.addEventListener("change", (e) => {
      previewContainer.innerHTML = "";
      const files = e.target.files;
      if (files) {
        Array.from(files).forEach(file => {
          if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = (event) => {
              const img = document.createElement("img");
              img.src = event.target.result;
              img.style.cssText = "width: 70px; height: 70px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1;";
              previewContainer.appendChild(img);
            };
            reader.readAsDataURL(file);
          }
        });
      }
    });
  }
});
