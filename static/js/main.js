document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Ad Popup Logic
    const adPopupModalElement = document.getElementById('adPopupModal');
    if (adPopupModalElement) {
        const adPopupModal = new bootstrap.Modal(adPopupModalElement);
        const showAdPopup = adPopupModalElement.dataset.showAdPopup === 'True';

        if (showAdPopup) {
            fetch('/get_popup_ad')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.ad) {
                        const ad = data.ad;
                        let adHtml = '';
                        if (ad.image_url) {
                            adHtml += `<img src="${ad.image_url}" class="img-fluid mb-3" alt="${ad.title}">`;
                        }
                        adHtml += `<h4>${ad.title}</h4>`;
                        adHtml += `<p>${ad.content}</p>`;
                        if (ad.link_url) {
                            adHtml += `<a href="${ad.link_url}" target="_blank" class="btn btn-primary">Learn More</a>`;
                        }
                        
                        document.getElementById('adPopupContent').innerHTML = adHtml;
                        adPopupModal.show();
                        
                        // Tell the server that the ad has been shown
                        fetch('/ad_popup_shown', { method: 'POST' });
                    }
                })
                .catch(error => console.error('Error fetching popup ad:', error));
        }
    }
});
