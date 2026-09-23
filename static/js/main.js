/**
 * Greeni5 - Main Client Script
 */

function initLucideIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

// Initialize immediately if DOM is already ready, or on events
if (document.readyState === "complete" || document.readyState === "interactive") {
  initLucideIcons();
} else {
  document.addEventListener("DOMContentLoaded", initLucideIcons);
}
window.addEventListener("load", initLucideIcons);

document.addEventListener("DOMContentLoaded", () => {
  initLucideIcons();

  // Toast Notification System
  window.showToast = function(message, type = "success", showCartLink = true) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 99999;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        pointer-events: none;
        width: 92%;
        max-width: 480px;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    const bgColor = type === "success" ? "#15803d" : type === "warning" ? "#d97706" : "#dc2626";
    toast.style.cssText = `
      background: ${bgColor};
      color: white;
      padding: 12px 18px;
      border-radius: 12px;
      box-shadow: 0 12px 35px rgba(0,0,0,0.25), inset 0 1px 1px rgba(255,255,255,0.4);
      font-size: 0.925rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      opacity: 0;
      transform: translateY(-20px);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: auto;
      width: 100%;
    `;

    let actionBtn = showCartLink && type === "success"
      ? `<a href="/cart" style="background: #ffffff; color: #15803d; padding: 6px 12px; border-radius: 8px; font-weight: 800; font-size: 0.85rem; text-decoration: none; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">View Cart 🛒 &rarr;</a>`
      : '';

    toast.innerHTML = `<span style="display: flex; align-items: center; gap: 8px;">✓ ${message}</span> ${actionBtn}`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "1";
      toast.style.transform = "translateY(0)";
    }, 10);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-20px)";
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  };

  // Mobile Navigation Menu Toggle
  const mobileToggle = document.querySelector(".mobile-menu-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener("click", () => {
      const isVisible = navLinks.style.display === "flex";
      navLinks.style.display = isVisible ? "none" : "flex";
      if (!isVisible) {
        navLinks.style.flexDirection = "column";
        navLinks.style.position = "absolute";
        navLinks.style.top = "74px";
        navLinks.style.left = "0";
        navLinks.style.width = "100%";
        navLinks.style.background = "#ffffff";
        navLinks.style.padding = "1.5rem";
        navLinks.style.borderBottom = "1px solid #d2edd9";
        navLinks.style.boxShadow = "0 10px 20px rgba(22, 163, 74, 0.1)";
      }
    });
  }

  // Wishlist / Favorites System (Stored in LocalStorage)
  function getWishlist() {
    try {
      return JSON.parse(localStorage.getItem("greeni5_wishlist") || "[]");
    } catch {
      return [];
    }
  }

  function updateWishlistBadge() {
    const list = getWishlist();
    const countEl = document.getElementById("wishlist-count");
    if (countEl) {
      countEl.textContent = list.length;
      countEl.style.display = list.length > 0 ? "flex" : "none";
    }

    document.querySelectorAll(".wishlist-toggle-btn").forEach(btn => {
      const pid = btn.dataset.plantId;
      if (list.includes(pid)) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  document.querySelectorAll(".wishlist-toggle-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const pid = btn.dataset.plantId;
      let list = getWishlist();

      if (list.includes(pid)) {
        list = list.filter(id => id !== pid);
        window.showToast("Removed plant from favorites", "warning");
      } else {
        list.push(pid);
        window.showToast("❤️ Plant saved to your favorites!", "success");
      }
      localStorage.setItem("greeni5_wishlist", JSON.stringify(list));
      updateWishlistBadge();
    });
  });

  updateWishlistBadge();

  // AJAX Add to Cart
  document.querySelectorAll(".ajax-add-to-cart").forEach(button => {
    button.addEventListener("click", async (e) => {
      e.preventDefault();
      const plantId = button.dataset.plantId;
      const qtyInput = document.getElementById("detail-quantity");
      const quantity = qtyInput ? qtyInput.value : 1;
      const variantInput = document.getElementById("selected-variant-id");
      const variantId = variantInput ? variantInput.value : "";
      const originalBtnContent = button.innerHTML;

      try {
        button.disabled = true;
        button.innerHTML = `<span>Adding...</span>`;

        const formData = new FormData();
        formData.append("quantity", quantity);
        if (variantId) {
          formData.append("variant_id", variantId);
        }

        const response = await fetch(`/cart/add/${plantId}`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          },
          body: formData
        });

        const data = await response.json();
        if (data.success) {
          window.showToast(data.message, "success", true);
          document.querySelectorAll(".cart-count").forEach(el => {
            if (el.id !== "wishlist-count") {
              el.textContent = data.cart_count;
              el.style.display = data.cart_count > 0 ? "flex" : "none";
            }
          });

          // Immediate button visual feedback
          button.style.background = "#15803d";
          button.innerHTML = `<span>✓ Added to Cart!</span>`;
          setTimeout(() => {
            button.disabled = false;
            button.style.background = "";
            button.innerHTML = originalBtnContent;
          }, 2000);
        } else {
          button.disabled = false;
          button.innerHTML = originalBtnContent;
          window.showToast(data.message || "Could not add to cart.", "warning", false);
        }
      } catch (err) {
        console.error("Cart error:", err);
        button.disabled = false;
        button.innerHTML = originalBtnContent;
        window.location.href = `/cart/add/${plantId}?quantity=${quantity}`;
      }
    });
  });

  // Plant Details Image Gallery Thumbnail Switcher
  const mainImage = document.getElementById("main-plant-image");
  const thumbnails = document.querySelectorAll(".thumb-item");
  if (mainImage && thumbnails.length > 0) {
    thumbnails.forEach(thumb => {
      thumb.addEventListener("click", () => {
        thumbnails.forEach(t => t.classList.remove("active"));
        thumb.classList.add("active");
        const newSrc = thumb.dataset.fullImg;
        if (newSrc) {
          mainImage.src = newSrc;
        }
      });
    });
  }

  // Quantity Stepper Controls
  document.querySelectorAll(".qty-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector(".qty-input");
      if (!input) return;
      let val = parseInt(input.value) || 1;
      const min = parseInt(input.min) || 1;
      const max = parseInt(input.max) || 99;

      if (btn.classList.contains("plus")) {
        if (val < max) val++;
      } else if (btn.classList.contains("minus")) {
        if (val > min) val--;
      }
      input.value = val;
      input.dispatchEvent(new Event("change"));
    });
  });

  // Saved Address autofill on checkout page
  const addressSelect = document.getElementById("saved-address-selector");
  if (addressSelect) {
    addressSelect.addEventListener("change", (e) => {
      const opt = e.target.selectedOptions[0];
      if (opt && opt.dataset.line) {
        document.getElementById("cust-name").value = opt.dataset.name || "";
        document.getElementById("cust-phone").value = opt.dataset.phone || "";
        document.getElementById("cust-addr").value = opt.dataset.line || "";
        document.getElementById("cust-city").value = opt.dataset.city || "";
        document.getElementById("cust-state").value = opt.dataset.state || "";
        document.getElementById("cust-pin").value = opt.dataset.pin || "";
      }
    });
  }

  // Plant Doctor Smart Care Calculator
  const calcBtn = document.getElementById("calc-btn");
  if (calcBtn) {
    calcBtn.addEventListener("click", () => {
      const room = document.getElementById("calc-room").value;
      const season = document.getElementById("calc-season").value;
      const resBox = document.getElementById("calc-results");
      const resTitle = document.getElementById("calc-res-title");
      const resDesc = document.getElementById("calc-res-desc");
      const resRec = document.getElementById("calc-res-recommend");

      let title = "Water Every 6-8 Days";
      let desc = "In standard living spaces with moderate filtered light, water thoroughly only when the top 2 inches of soil feel dry. Wipe broad leaves once a month to keep pores unclogged.";
      let rec = "Top Recommended: Monstera Deliciosa, Peace Lily, Areca Palm";

      if (room === "bedroom" || room === "desk") {
        if (season === "winter") {
          title = "Water Sparingly (Every 12-14 Days)";
          desc = "Indoor low light combined with cooler winter temperatures slows soil moisture evaporation. Check topsoil deeply before adding any water.";
        } else {
          title = "Water Every 9-11 Days";
          desc = "Low-light office and bedroom corners require less frequent drinks. Use a spray bottle to mist foliage gently for humidity.";
        }
        rec = "Top Recommended: Snake Plant Golden Hahnii, Peace Lily, Holy Basil";
      } else if (room === "balcony") {
        if (season === "summer") {
          title = "Water Daily (Every 1-2 Days)";
          desc = "Outdoor balconies facing afternoon sun dry out rapidly in the summer heat. Water early in the morning before the sun peaks.";
        } else {
          title = "Water Every 3-4 Days";
          desc = "Good air circulation outdoors keeps roots healthy. Ensure planter drainage holes are completely clear.";
        }
        rec = "Top Recommended: Bougainvillea, Mogra Jasmine, Hibiscus, Kagzi Lemon";
      }

      resTitle.textContent = title;
      resDesc.textContent = desc;
      resRec.textContent = "🌱 " + rec;
      resBox.style.display = "block";
  // Live Flash Sale Countdown Clock
  const flashTimer = document.getElementById("flash-sale-timer");
  if (flashTimer && flashTimer.dataset.endtime) {
    function tickSale() {
      const end = new Date(flashTimer.dataset.endtime).getTime();
      const now = new Date().getTime();
      const diff = end - now;
      if (diff <= 0) {
        flashTimer.textContent = "00:00:00 (Sale Concluded)";
        return;
      }
      const hrs = Math.floor(diff / (1000 * 60 * 60));
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const secs = Math.floor((diff % (1000 * 60)) / 1000);
      flashTimer.textContent = `${String(hrs).padStart(2, "0")}h ${String(mins).padStart(2, "0")}m ${String(secs).padStart(2, "0")}s`;
    }
    tickSale();
    setInterval(tickSale, 1000);
  }

  // Pot Variant Selector on Plant Details Page
  const variantPills = document.querySelectorAll(".pot-variant-pill");
  const basePriceEl = document.getElementById("details-display-price");
  const selectedVariantInput = document.getElementById("selected-variant-id");
  if (variantPills.length > 0 && basePriceEl) {
    const originalPrice = parseFloat(basePriceEl.dataset.basePrice || "0");
    variantPills.forEach(pill => {
      pill.addEventListener("click", () => {
        variantPills.forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        const extra = parseFloat(pill.dataset.extraPrice || "0");
        const newTotal = originalPrice + extra;
        basePriceEl.textContent = "₹" + Math.round(newTotal);
        if (selectedVariantInput) {
          selectedVariantInput.value = pill.dataset.variantId;
        }
      });
    });
  }
});
