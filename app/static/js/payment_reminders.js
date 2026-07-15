document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".reminder-page");
    const modal = document.querySelector("[data-reminder-modal]");
    if (!page || !modal) return;

    const customerId = modal.querySelector("[data-modal-customer-id]");
    const channelInput = modal.querySelector("[data-modal-channel]");
    const mobileInput = modal.querySelector("[data-modal-mobile]");
    const emailInput = modal.querySelector("[data-modal-email]");
    const customerLabel = modal.querySelector("[data-modal-customer]");
    const balanceLabel = modal.querySelector("[data-modal-balance]");
    const messageInput = modal.querySelector("[data-modal-message]");
    const followupInput = modal.querySelector("[data-modal-followup]");
    const sendButton = modal.querySelector("[data-modal-send]");
    const sendLabel = sendButton.querySelector("span");
    const companyName = page.dataset.companyName || "our company";

    const closeModal = () => {
        modal.hidden = true;
        document.body.style.overflow = "";
    };

    document.querySelectorAll("[data-reminder-close]").forEach((button) => button.addEventListener("click", closeModal));

    document.querySelectorAll("[data-reminder-open]").forEach((button) => {
        button.addEventListener("click", () => {
            const balance = Number(button.dataset.balance || 0);
            const formattedBalance = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(balance);
            customerId.value = button.dataset.customerId;
            channelInput.value = button.dataset.channel;
            mobileInput.value = button.dataset.mobile;
            emailInput.value = button.dataset.email;
            customerLabel.textContent = button.dataset.customer;
            balanceLabel.textContent = formattedBalance;
            messageInput.value = `Dear ${button.dataset.customer}, this is a payment reminder from ${companyName}. Our records show a pending balance of ${formattedBalance}. Kindly arrange payment at the earliest or contact us if payment has already been made. Thank you.`;
            sendLabel.textContent = `Open ${button.dataset.channel}`;
            modal.hidden = false;
            document.body.style.overflow = "hidden";
            messageInput.focus();
        });
    });

    const normalizePhone = (value) => {
        let digits = String(value || "").replace(/\D/g, "");
        if (digits.length === 10) digits = `91${digits}`;
        return digits;
    };

    const showToast = () => {
        const toast = document.querySelector("[data-reminder-toast]");
        if (!toast) return;
        toast.hidden = false;
        window.setTimeout(() => { toast.hidden = true; }, 3500);
    };

    sendButton.addEventListener("click", () => {
        const channel = channelInput.value;
        const message = messageInput.value.trim();
        const mobile = normalizePhone(mobileInput.value);
        const email = emailInput.value.trim();
        if (!message) {
            messageInput.focus();
            return;
        }

        let destination = "";
        if (channel === "WhatsApp") destination = `https://wa.me/${mobile}?text=${encodeURIComponent(message)}`;
        if (channel === "SMS") destination = `sms:${mobile}?body=${encodeURIComponent(message)}`;
        if (channel === "Email") destination = `mailto:${email}?subject=${encodeURIComponent("Payment Reminder")}&body=${encodeURIComponent(message)}`;

        const logData = new URLSearchParams({
            customer_id: customerId.value,
            channel,
            message,
            next_followup_date: followupInput.value
        });
        fetch("/payment-reminders/log", { method: "POST", body: logData, keepalive: true })
            .then((response) => {
                if (!response.ok) throw new Error("Unable to record reminder");
                showToast();
            })
            .catch(() => {});

        if (channel === "WhatsApp") window.open(destination, "_blank", "noopener");
        else window.location.href = destination;

        closeModal();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.hidden) closeModal();
    });
});
