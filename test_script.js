
        const API_BASE = "http://localhost:8080";
        let selectedFile = null;

        function getParam(name) {
            try { return new URLSearchParams(window.location.search).get(name); } catch(e){ return null; }
        }

        function handleFileSelect(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                if (file.size > 10 * 1024 * 1024) {
                    showToast('File quá lớn! Vui lòng chọn ảnh dưới 10MB.', 'error');
                    return;
                }
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('preview-img').src = e.target.result;
                    document.getElementById('upload-zone').style.display = 'none';
                    document.getElementById('preview-container').style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        }

        function removeImage(e) {
            e.stopPropagation();
            selectedFile = null;
            document.getElementById('file-input').value = '';
            document.getElementById('upload-zone').style.display = 'block';
            document.getElementById('preview-container').style.display = 'none';
        }

        async function fetchRecommendations() {
            if (!selectedFile) {
                showToast('Vui lòng tải ảnh người lên trước!', 'error');
                return;
            }

            const runBtn = document.getElementById('run-btn');
            const loading = document.getElementById('loading-overlay');
            const statusText = document.getElementById('loading-status');
            const loadingTitle = document.getElementById('loading-title');

            try {
                runBtn.disabled = true;
                loading.style.display = 'flex';
                loadingTitle.innerHTML = '<i class="fas fa-search"></i> Đang tìm kiếm tủ đồ...';
                statusText.textContent = "Hệ thống đang quét các sản phẩm Normalized phù hợp nhất...";

                const formData = new FormData();
                formData.append('gender', document.getElementById('gender').value);
                formData.append('occasion', document.getElementById('occasion').value);
                formData.append('style', document.getElementById('style').value);
                formData.append('body_shape', document.getElementById('body_shape').value);
                formData.append('budget', document.getElementById('budget').value);
                formData.append('outfit_type', document.getElementById('outfit_type').value);

                const response = await fetch(`${API_BASE}/api/recommend-products`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                loading.style.display = 'none';
                runBtn.disabled = false;

                if (data.success) {
                    if(!data.results || data.results.length === 0){
                        showToast('Không tìm thấy đồ phù hợp. Hãy thử thay đổi Ngân sách/Dáng người.', 'error');
                    } else {
                        showRecommendations(data.results, data.outfit_type);
                    }
                } else {
                    showToast(data.message || 'Lỗi lấy gợi ý', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Lỗi kết nối máy chủ API.', 'error');
                runBtn.disabled = false;
                loading.style.display = 'none';
            }
        }

        function showRecommendations(results, outfitType) {
            document.getElementById('result-empty').style.display = 'none';
            document.getElementById('result-filled').style.display = 'block';
            
            // Ẩn ảnh VTON tạm thời
            document.querySelector('.main-result-img').style.display = 'none';
            document.getElementById('triedOutfitBanner').style.display = 'none';
            
            const container = document.getElementById('outfit-cards');
            container.innerHTML = '';
            
            document.querySelector('.recommend-title').innerHTML = `<i class="fas fa-check-circle"></i> Vui lòng chọn 1 thẻ để "Thử lên người"`;
            
            results.forEach((res, index) => {
                const card = document.createElement('div');
                card.className = 'outfit-card';
                card.style.cursor = 'pointer';
                card.style.transition = 'transform 0.2s, box-shadow 0.2s';
                card.onmouseover = () => { card.style.transform = 'scale(1.03)'; card.style.boxShadow = '0 8px 15px rgba(0,0,0,0.1)'; };
                card.onmouseout = () => { card.style.transform = 'scale(1)'; card.style.boxShadow = 'none'; };
                
                // When clicking a card, run Phase 2
                card.onclick = () => runTryOnPhase2(res.items);
                
                if (res.type === 'single') {
                    const item = res.items[0];
                    card.innerHTML = `
                        <img src="${item.image_url}" alt="${item.name}" onerror="this.src='https://placehold.co/200x260?text=No+Image'">
                        <div class="outfit-info">
                            <div class="name">${item.name}</div>
                            <div class="price">${formatPrice(item.price)}</div>
                            <div class="shopee-tag">✨ BẤM ĐỂ THỬ</div>
                        </div>
                    `;
                } else {
                    const top = res.items[0];
                    const bot = res.items[1];
                    card.innerHTML = `
                        <div style="display:flex; height: 140px; border-bottom: 2px solid #f0f0f0;">
                            <img src="${top.image_url}" style="width:50%; object-fit:cover; border-right: 1px solid #f0f0f0;" title="${top.name}">
                            <img src="${bot.image_url}" style="width:50%; object-fit:cover;" title="${bot.name}">
                        </div>
                        <div class="outfit-info">
                            <div class="name"><b>Set kết hợp:</b> ${top.name.substring(0, 15)}... + Quần/Váy</div>
                            <div class="price">COMBO Đôi</div>
                            <div class="shopee-tag" style="background-color:#E91E63;">✨ THỬ CẢ BỘ</div>
                        </div>
                    `;
                }
                container.appendChild(card);
            });

            document.getElementById('result-filled').scrollIntoView({ behavior: 'smooth' });
            showToast('Đã lọc ra đồ phù hợp. Vui lòng bấm vào 1 thẻ bài!', 'success');
        }

        async function runTryOnPhase2(garments) {
            const loading = document.getElementById('loading-overlay');
            const statusText = document.getElementById('loading-status');
            const loadingTitle = document.getElementById('loading-title');

            try {
                loading.style.display = 'flex';
                loadingTitle.innerHTML = '✨ AI Đang May Đo...';
                statusText.textContent = "Kết nối công nghệ FASHN VTON 1.5 với 100% Ảnh gốc của bạn...";

                const formData = new FormData();
                formData.append('photo', selectedFile);
                formData.append('garments', JSON.stringify(garments)); // Serialize mảng garments

                const response = await fetch(`${API_BASE}/api/virtual-tryon`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success && data.task_id) {
                    pollTaskStatus(data.task_id);
                } else {
                    showToast(data.message || 'Có lỗi xảy ra', 'error');
                    loading.style.display = 'none';
                }
            } catch (err) {
                console.error(err);
                showToast('Lỗi kết nối máy chủ AI VTON.', 'error');
                loading.style.display = 'none';
            }
        }

        async function pollTaskStatus(taskId) {
            const statusText = document.getElementById('loading-status');
            const loading = document.getElementById('loading-overlay');
            
            let attempts = 0;
            const maxAttempts = 150; // 5 phút max

            const interval = setInterval(async () => {
                attempts++;
                if (attempts > maxAttempts) {
                    clearInterval(interval);
                    showToast('Yêu cầu hết thời gian chờ. Vui lòng thử lại.', 'error');
                    loading.style.display = 'none';
                    return;
                }

                try {
                    const res = await fetch(`${API_BASE}/api/virtual-tryon/status/${taskId}`);
                    const data = await res.json();

                    if (data.status === 'completed') {
                        clearInterval(interval);
                        showFinalResult(data);
                        showToast('Thành công! Trả kết quả ảnh gốc...', 'success');
                        loading.style.display = 'none';
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        showToast(data.message || 'AI xử lý thất bại.', 'error');
                        loading.style.display = 'none';
                    } else {
                        statusText.textContent = data.message || "Đang xử lý mô phỏng 4K...";
                    }
                } catch (err) {
                    console.error("Polling error:", err);
                }
            }, 2500);
        }

        function showFinalResult(data) {
            document.querySelector('.main-result-img').style.display = 'block';
            document.getElementById('result-img').src = data.result_image_url + "?nocache=" + Date.now();
            
            if (data.tried_items && data.tried_items.length > 0) {
                const banner = document.getElementById('triedOutfitBanner');
                
                let html = "<div style='margin-bottom: 8px;'><strong>🛒 GIỎ HÀNG BẠN ĐANG MẶC TRÊN ẢNH:</strong></div>";
                data.tried_items.forEach(t => {
                    html += `
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; border-bottom: 1px solid #ffe0b2; padding-bottom: 5px;'>
                            <span style="font-weight: 500; font-size: 0.95rem;">${t.name}</span>
                            <a href="${t.url}" target="_blank" style="margin-left:5px; color: var(--rose); font-weight: bold; text-decoration: none; padding: 5px 12px; border: 1.5px solid var(--rose); border-radius: 6px; font-size: 0.8rem;">Mua ngay</a>
                        </div>
                    `;
                });
                
                banner.innerHTML = html;
                banner.style.display = 'block';
            }

            document.getElementById('result-filled').scrollIntoView({ behavior: 'smooth' });
        }

        function openShopee(url) {
            if (url && url !== '#' && url.startsWith('http')) {
                window.open(url, '_blank', 'noopener');
            } else {
                showToast('Sản phẩm này chưa có link Shopee.', 'error');
            }
        }

        function formatPrice(p) {
            if (!p && p !== 0) return '';
            return Number(p).toLocaleString('vi-VN') + 'đ';
        }

        function showToast(msg, type) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = `toast show ${type}`;
            setTimeout(() => {
                t.className = 'toast';
            }, 3500);
        }

        // Navbar submenu actions (from index.html dropdown)
        (function initNavAction() {
            const gt = (getParam('garment_type') || '').toLowerCase();
            if (gt && document.getElementById('garment_type')) {
                document.getElementById('garment_type').value = gt;
            }
            const action = (getParam('action') || '').toLowerCase();
            if (action === 'upload') {
                setTimeout(() => {
                    const z = document.getElementById('upload-zone');
                    if (z) z.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    showToast('Chọn ảnh để bắt đầu Try-On', 'success');
                    document.getElementById('file-input')?.click();
                }, 350);
            } else if (action === 'garment') {
                setTimeout(() => {
                    document.getElementById('garment_type')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    showToast('Chọn loại đồ rồi nhấn Magic', 'success');
                }, 350);
            } else if (action === 'result') {
                setTimeout(() => {
                    const filled = document.getElementById('result-filled');
                    if (filled && filled.style.display !== 'none') {
                        filled.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else {
                        showToast('Vui lòng upload ảnh và nhấn Magic trước', 'error');
                    }
                }, 350);
            } else if (action === 'compare') {
                setTimeout(() => showToast('Tính năng đang phát triển', 'error'), 200);
            }
        })();

        // Drag & Drop & Click
        const zone = document.getElementById('upload-zone');
        zone.addEventListener('click', () => document.getElementById('file-input').click());
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
            zone.addEventListener(evt, e => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        zone.addEventListener('drop', e => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                const input = document.getElementById('file-input');
                input.files = files;
                handleFileSelect(input);
            }
        });
    