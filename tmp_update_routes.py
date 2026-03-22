import os
import shutil

rt_path = 'c:/Mai/4/backend/app/routes.py'
shutil.copyfile(rt_path, rt_path + '.bak2')

with open(rt_path, 'r', encoding='utf-8') as f:
    text = f.read()

prefix = text.split('def _run_vton_pipeline(')[0]
suffix = text.split('def virtual_tryon_status(')[1]

new_code = '''def _resolve_clean_abs(clean_rel, static_folder_path):
    import os
    if not clean_rel: return None
    try:
        rel = str(clean_rel).lstrip("/").replace("\\\\", "/")
        if not rel.startswith("static"):
            abs_path = os.path.abspath(os.path.join(static_folder_path, rel))
        else:
            rel_clean = rel.replace("static/", "", 1)
            abs_path = os.path.abspath(os.path.join(static_folder_path, rel_clean))
        if os.path.exists(abs_path): return abs_path
        if os.path.exists(clean_rel): return clean_rel
    except: pass
    return None

def _run_vton_pipeline_v2(in_path, garments, results_dir, out_path, static_folder_path):
    import time
    t_start = time.time()
    
    # User Requirement: KHÔNG xóa nền ảnh người. Gửi nguyên bản.
    person_path = in_path
    final_path = in_path
    
    tried_items = []
    
    for g in garments:
        garment_img_url = g.get('image_url')
        clean_path_rel = g.get('clean_image_path')
        db_cat = g.get('category') or g.get('garment_type') or 'upper_body'
        
        fashn_cat = "tops"
        if any(k in db_cat.lower() for k in ["dress", "one-piece", "váy", "đầm"]): fashn_cat = "one-pieces"
        elif any(k in db_cat.lower() for k in ["bottom", "quan", "quần", "skirt", "trouser", "jean", "short"]): fashn_cat = "bottoms"

        shopee_url = g.get('shopee_url', '')
        name = g.get('name', 'Product')
        
        print(f"[TRYON] Đang xử lý: {name} ({fashn_cat})")
        
        g_abs = _resolve_clean_abs(clean_path_rel, static_folder_path)
        
        if not g_abs:
            g_abs = download_garment_image(garment_img_url, shopee_url, save_dir=os.path.join(static_folder_path, 'uploads', 'tryon'))
            
        if g_abs and os.path.exists(g_abs):
            try:
                res_path, fb = call_fashn_vton(person_path, g_abs, category=fashn_cat)
                if not fb:
                    person_path = res_path
                    final_path = res_path
                    tried_items.append({"name": name, "url": shopee_url, "image_url": garment_img_url, "price": g.get("price")})
            except Exception as e:
                print(f"[TRYON] ⚠️ Lỗi khi gọi VTON cho {name}: {e}")
                
    import shutil
    shutil.copyfile(final_path, out_path)
    print(f"[TRYON] [{time.time() - t_start:.1f}s] ✅ Hoàn tất Try-On -> {out_path}")
    return {"path": out_path, "is_fallback": False, "tried_items": tried_items}

@main_bp.route('/api/recommend-products', methods=['POST'])
def recommend_products_api():
    try:
        outfit_type = (request.form.get('outfit_type') or request.json.get('outfit_type') or 'dress').strip()
        gender = request.form.get('gender') or request.json.get('gender') or 'female'
        occasion = request.form.get('occasion') or request.json.get('occasion') or 'casual'
        style = request.form.get('style') or request.json.get('style') or 'any'
        
        garment_type = 'dress'
        if outfit_type == 'top_bottom':
            garment_type = 'any'
            
        recommended = get_recommended_outfits(
            gender=gender,
            occasion=occasion,
            style=style,
            body_shape=request.form.get('body_shape') or request.json.get('body_shape') or '',
            budget=request.form.get('budget') or request.json.get('budget') or 'any',
            garment_type=garment_type,
            limit=40,
        )
        
        if not recommended:
            recommended = _get_demo_products()
            
        valid_products = [p for p in recommended if p.get('clean_image_path')]
        
        results = []
        if outfit_type == 'dress':
            dresses = [p for p in valid_products if any(k in str(p.get("garment_type") or "").lower() for k in ["dress", "one-piece", "váy", "đầm", "jumpsuit"])]
            if not dresses:
                dresses = valid_products[:12]
            results = [{"type": "single", "items": [d]} for d in dresses]
            
        elif outfit_type == 'top_bottom':
            tops = [p for p in valid_products if any(k in str(p.get("garment_type") or "").lower() for k in ["top", "ao", "áo", "shirt", "t-shirt", "vest", "khoác"])]
            bottoms = [p for p in valid_products if any(k in str(p.get("garment_type") or "").lower() for k in ["bottom", "quan", "quần", "pants", "short", "jeans", "trouser", "skirt"])]
            
            paired = []
            min_len = min(len(tops), len(bottoms))
            for i in range(min_len):
                paired.append({
                    "type": "pair",
                    "items": [tops[i], bottoms[i]]
                })
            results = paired
            
        return jsonify({
            'success': True,
            'outfit_type': outfit_type,
            'results': results
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/virtual-tryon', methods=['POST'])
def virtual_tryon_api():
    import json
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'message': 'photo is required'}), 400
            
        photo = request.files['photo']
        garments_json = request.form.get('garments')
        
        garments = []
        if garments_json:
            try:
                garments = json.loads(garments_json)
            except:
                pass
                
        if not garments:
            return jsonify({'success': False, 'message': 'Không tìm thấy thông tin sản phẩm (garments missing)'}), 400

        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'tryon')
        results_dir = os.path.join(current_app.static_folder, 'static', 'tryon_results')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)

        ext = os.path.splitext(photo.filename)[1].lower() or '.jpg'
        in_name = f"{uuid.uuid4().hex}{ext}"
        in_path = os.path.join(upload_dir, in_name)
        photo.save(in_path)

        out_name = f"result_{uuid.uuid4().hex}.jpg"
        out_path = os.path.join(results_dir, out_name)

        task_id = vton_processor_queue.add_task(
            _run_vton_pipeline_v2,
            in_path, garments, results_dir, out_path, current_app.static_folder
        )

        return jsonify({
            "success": True,
            "task_id": task_id,
            "status": "pending",
            "message": "AI Đang xử lý phối đồ..."
        }), 202

    except Exception as e:
        print(f"[API] Error: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@main_bp.route('/api/virtual-tryon/status/<task_id>', methods=['GET'])
def virtual_tryon_status('''

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(prefix + new_code + suffix)

print("ROUTES UPDATED SUCCESSFULLY!")
