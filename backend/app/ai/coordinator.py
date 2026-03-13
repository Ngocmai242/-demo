import random
from ..models import Product, ItemType, Category, Style, Color
from flask import current_app

class OutfitCoordinator:
    """
    Smart recommendation engine for outfit coordination.
    Uses an advanced hybrid approach: 
    1. Static Fashion Rules (Color Theory & Style Logic)
    2. Category Compatibility (Tops vs Bottoms vs Outerwear)
    3. Occasion & Season alignment.
    """
    
    # Advanced Color Compatibility Theory
    # We use a mix of Complementary, Analogous, and Neutral rules.
    COLOR_RULES = {
        'Black': {
            'matches': ['White', 'Gray', 'Red', 'Blue', 'Pink', 'Yellow', 'Beige', 'Gold', 'Silver'],
            'description': 'Universal neutral, matches almost everything.'
        },
        'White': {
            'matches': ['Black', 'Navy', 'Blue', 'Pink', 'Gray', 'Brown', 'Green', 'Red', 'Beige'],
            'description': 'Universal neutral, creates high contrast.'
        },
        'Beige': {
            'matches': ['White', 'Navy', 'Brown', 'Green', 'Black', 'Blue', 'Olive'],
            'description': 'Earthy neutral, works well with other natural tones.'
        },
        'Navy': {
            'matches': ['White', 'Beige', 'Gray', 'Red', 'Pink', 'Yellow', 'Blue'],
            'description': 'Classic formal color, great with warm accents.'
        },
        'Pink': {
            'matches': ['White', 'Black', 'Gray', 'Navy', 'Blue', 'Red'],
            'description': 'Vibrant, works best with neutrals or complementary blue/navy.'
        },
        'Blue': {
            'matches': ['White', 'Black', 'Gray', 'Beige', 'Navy', 'Orange', 'Yellow'],
            'description': 'Versatile, blue and orange are complementary.'
        },
        'Red': {
            'matches': ['White', 'Black', 'Navy', 'Gray', 'Beige', 'Blue'],
            'description': 'Bold, works well with dark neutrals.'
        },
        'Brown': {
            'matches': ['White', 'Beige', 'Green', 'Navy', 'Yellow', 'Cream'],
            'description': 'Warm neutral, matches forest and earth tones.'
        },
        'Green': {
            'matches': ['White', 'Beige', 'Black', 'Brown', 'Yellow', 'Pink'],
            'description': 'Natural, works well with earth tones or pink (complementary).'
        },
        'Multicolor': {
            'matches': ['White', 'Black', 'Navy', 'Gray', 'Beige'],
            'description': 'Patterned items work best with solid neutrals.'
        }
    }

    # Specific Occasion Rules
    OCCASION_THEMES = {
        'Tet': {
            'colors': ['Red', 'Yellow', 'Gold', 'Pink', 'Cream'],
            'styles': ['Elegant', 'Formal', 'Traditional', 'Luxury'],
            'description': 'Bright and lucky colors for Lunar New Year.'
        },
        'Noel': {
            'colors': ['Red', 'Green', 'White', 'Silver', 'Gold'],
            'styles': ['Casual', 'Sporty', 'Sweet', 'Vintage'],
            'description': 'Festive and cozy colors for Christmas.'
        },
        'Work': {
            'colors': ['Navy', 'Black', 'White', 'Gray', 'Beige', 'Blue', 'Brown'],
            'styles': ['Office', 'Formal', 'Minimal', 'Classic'],
            'description': 'Professional and clean colors.'
        },
        'Party': {
            'colors': ['Black', 'Silver', 'Gold', 'Red', 'Purple', 'Pink'],
            'styles': ['Elegant', 'Party', 'Sexy', 'Y2K', 'Luxury'],
            'description': 'Stunning and bold colors for events.'
        },
        'School': {
            'colors': ['White', 'Blue', 'Gray', 'Beige', 'Multicolor'],
            'styles': ['Minimal', 'Basic', 'Casual', 'Sporty', 'Preppy'],
            'description': 'Comfortable and youthful styles.'
        },
        'Play': {
            'colors': ['Multicolor', 'Pink', 'Green', 'Blue', 'Yellow', 'Sky blue'],
            'styles': ['Streetwear', 'Casual', 'Sporty', 'Y2K', 'Vintage'],
            'description': 'Dynamic and expressive styles for outings.'
        }
    }

    # Body Shape Optimization Rules
    # Logic: Prioritize certain categories/fits for each body type
    BODY_SHAPE_RULES = {
        'Hourglass': {
            'boost_fits': ['Slim fit', 'Body fit', 'Regular fit'],
            'preferred_types': ['dress', 'belt', 'high-waist'],
            'description': 'Focus on maintaining balance and highlighting the waist.'
        },
        'Pear': {
            'boost_fits': ['Regular fit', 'Oversize'], # Boost upper body volume
            'preferred_types': ['top', 'jacket', 'blazer'], # Focus upper body
            'avoid_keywords': ['skinny', 'tight-bottom'],
            'description': 'Draw attention to the upper body to balance wider hips.'
        },
        'Apple': {
            'boost_fits': ['Loose fit', 'Regular fit'],
            'preferred_types': ['top', 'outerwear', 'v-neck'], # Emphasize legs/bust
            'avoid_keywords': ['cropped', 'tight-waist'],
            'description': 'Focus on vertical lines and showing off legs.'
        },
        'Rectangle': {
            'boost_fits': ['Regular fit', 'Slim fit'],
            'preferred_types': ['peplum', 'skirt', 'ruffles', 'belt'],
            'description': 'Create curves with volume and waist definition.'
        },
        'Inverted Triangle': {
            'boost_fits': ['Regular fit', 'Wide-leg'],
            'preferred_types': ['bottom', 'skirt', 'pants', 'wide-leg'], # Focus lower body
            'avoid_keywords': ['structured-shoulders', 'blazer'],
            'description': 'Balance broad shoulders by adding volume to the lower body.'
        }
    }

    # Style compatibility logic - allowing for stylistic overlaps
    STYLE_MATRIX = {
        'Casual': ['Streetwear', 'Minimal', 'Vintage', 'Basic', 'Athleisure'],
        'Office': ['Formal', 'Minimal', 'Elegant', 'Classic'],
        'Streetwear': ['Casual', 'Y2K', 'Sporty', 'Hiphop', 'Grunge'],
        'Elegant': ['Formal', 'Party', 'Luxury', 'Minimal', 'Chic'],
        'Minimal': ['Casual', 'Office', 'Elegant', 'Vintage', 'Modern'],
        'Vintage': ['Retro', 'Casual', 'Classic', 'Boho'],
        'Sporty': ['Casual', 'Athleisure', 'Streetwear'],
        'Party': ['Elegant', 'Sexy', 'Y2K', 'Nightout'],
        'Y2K': ['Streetwear', 'Party', 'Cyber'],
    }

    @staticmethod
    def get_recommendations(target_product, body_shape=None, occasion=None, limit=12):
        """
        Smart algorithm to find compatible products.
        Score is calculated based on:
        - Category Logic (Bottom matches Top, etc.) -> 40 pts
        - Style Synergy (Matches base or matrix) -> 20 pts
        - Color Harmony (Color rules) -> 15 pts
        - Occasion Theme (Tet, Noel, etc.) -> 15 pts (NEW)
        - Body Shape Compatibility -> 10 pts (NEW)
        """
        try:
            # 1. Identify valid categories for coordination
            cat_name = (target_product.category_label or '').lower()
            it_name = (target_product.item_type.name if target_product.item_type else '').lower()
            
            # Search logic for different types
            targets = []
            if it_name == 'top' or 'top' in cat_name:
                targets = ['bottom', 'bottoms', 'pants', 'skirt', 'shorts']
            elif it_name == 'bottom' or 'bottom' in cat_name or 'pants' in cat_name:
                targets = ['top', 'tops', 'shirt', 'jacket', 'blazer', 'hoodie']
            elif it_name == 'dress' or 'dress' in cat_name:
                targets = ['outerwear', 'jacket', 'shoes', 'bag']
            elif it_name == 'outerwear' or 'jacket' in cat_name:
                targets = ['top', 'bottom', 'pants', 't-shirt']
            else:
                targets = ['top', 'bottom', 'accessory']

            # 2. Query candidates
            query = Product.query.filter(Product.id != target_product.id, Product.is_active == True)
            
            # Gender matching (strict unless unisex)
            if target_product.gender and target_product.gender != 'Unisex':
                query = query.filter((Product.gender == target_product.gender) | (Product.gender == 'Unisex'))
            
            candidates = query.all()
            scored_list = []

            for p in candidates:
                score = 0
                p_cat = (p.category_label or '').lower()
                p_it = (p.item_type.name if p.item_type else '').lower()
                p_style = p.style_label or (p.style_ref.name if p.style_ref else 'Casual')
                p_color = p.color_label or (p.color.name if p.color else 'Black')
                p_fit = (p.fit_type or 'Regular fit')

                # --- A. Category Logic (40 pts) ---
                if any(t in p_cat or t in p_it for t in targets):
                    score += 40

                # --- B. Style Synergy (20 pts) ---
                t_style = target_product.style_label or (target_product.style_ref.name if target_product.style_ref else 'Casual')
                if p_style == t_style:
                    score += 20
                elif p_style in OutfitCoordinator.STYLE_MATRIX.get(t_style, []):
                    score += 10
                
                # --- C. Color Harmony (15 pts) ---
                t_color = target_product.color_label or (target_product.color.name if target_product.color else 'Black')
                if p_color == t_color:
                    score += 5 
                elif p_color in OutfitCoordinator.COLOR_RULES.get(t_color, {}).get('matches', []):
                    score += 15
                
                # --- D. Occasion Theme (15 pts) --- (NEW)
                if occasion and occasion in OutfitCoordinator.OCCASION_THEMES:
                    theme = OutfitCoordinator.OCCASION_THEMES[occasion]
                    # Check if color matches theme
                    if p_color in theme['colors']:
                        score += 10
                    # Check if style matches theme
                    if p_style in theme['styles']:
                        score += 5
                else:
                    # Default: Match target occasion label
                    p_occ = p.occasion_label or (p.occasion_ref.name if p.occasion_ref else '')
                    t_occ = target_product.occasion_label or (target_product.occasion_ref.name if target_product.occasion_ref else '')
                    if p_occ == t_occ and p_occ != '':
                        score += 10

                # --- E. Body Shape Compatibility (10 pts) --- (NEW)
                if body_shape and body_shape in OutfitCoordinator.BODY_SHAPE_RULES:
                    shape_rule = OutfitCoordinator.BODY_SHAPE_RULES[body_shape]
                    # Boost preferred fits
                    if p_fit in shape_rule['boost_fits']:
                        score += 6
                    # Boost preferred types
                    if any(pt in p_cat for pt in shape_rule['preferred_types']):
                        score += 4
                
                scored_list.append((p.id, score))

            # Sort by score and return IDs
            scored_list.sort(key=lambda x: x[1], reverse=True)
            return [sid for sid, sc in scored_list[:limit]]

        except Exception as e:
            current_app.logger.error(f"Coordinator Err: {e}")
            return []

    @staticmethod
    def get_outfit_for_person(body_shape, occasion=None, gender='Unisex', preferred_style=None, limit=3):
        """
        Generates a complete outfit for a person from scratch.
        Ideal for Personal AI Stylist.
        """
        current_app.logger.info(f"AI Styling Request: Shape={body_shape}, Occasion={occasion}, Gender={gender}, Style={preferred_style}")
        try:
            # 1. Base Query
            query = Product.query.filter((Product.is_active == True) | (Product.is_active == None))
            
            # Category priority for Hero item
            hero_types = ['top', 'dress', 'set', 'jumpsuit', 'matching_set', 'tops', 'dresses_skirts', 'clothing_sets', 'shirt', 'vay']
            query_hero = query.filter(Product.item_type.has(db.func.lower(ItemType.name).in_(hero_types)))
            
            # Gender filter
            gender_filter = (Product.gender == gender) | (Product.gender == 'Unisex')
            if gender == 'Unisex': gender_filter = True # No filter
            
            prods = query_hero.filter(gender_filter).all()
            
            # Fallbacks to ensure we have products to work with
            if not prods: prods = query_hero.all() # Try any hero item
            if not prods: prods = query.all() # Try any item
            if not prods: prods = Product.query.all() # Last resort: any product at all

            if not prods:
                current_app.logger.error("Database is EMPTY.")
                return []

            # Score candidates for Hero item
            scored_heroes = []
            for p in prods:
                score = 0
                p_it = (p.item_type.name if p.item_type else '').lower()
                p_style = p.style_label or (p.style_ref.name if p.style_ref else 'Casual')
                p_color = (p.color_label or (p.color.name if p.color else 'Black')).strip().capitalize()
                p_fit = (p.fit_type or 'Regular fit')
                p_cat = (p.category_label or '').lower()

                # Occasion Theme (HIGH PRIORITY) - Target Noel colors even if not labeled
                if occasion and occasion in OutfitCoordinator.OCCASION_THEMES:
                    theme = OutfitCoordinator.OCCASION_THEMES[occasion]
                    # Direct color match boost
                    if any(c.capitalize() == p_color for c in theme['colors']):
                        score += 40 
                    if p_style in theme['styles']:
                        score += 15
                
                # Shape
                if body_shape and body_shape in OutfitCoordinator.BODY_SHAPE_RULES:
                    rule = OutfitCoordinator.BODY_SHAPE_RULES[body_shape]
                    if p_fit in rule['boost_fits']: score += 10
                    if any(pt in p_cat or pt in p_it for pt in rule['preferred_types']): score += 5
                
                # Style Preference
                if preferred_style:
                    if p_style == preferred_style:
                        score += 20
                    elif p_style in OutfitCoordinator.STYLE_MATRIX.get(preferred_style, []):
                        score += 10

                scored_heroes.append((p, score + random.randint(1, 10)))

            # Sort and select best Hero
            scored_heroes.sort(key=lambda x: x[1], reverse=True)
            hero = scored_heroes[0][0]
            current_app.logger.info(f"Selected HERO: {hero.name} (Score: {scored_heroes[0][1]})")
            
            # 2. Complete the outfit
            recs = OutfitCoordinator.get_recommendations(hero, body_shape=body_shape, occasion=occasion, limit=limit-1)
            
            # CRITICAL FALLBACK: If coordination engine fails to find matches (e.g. no bottoms in DB),
            # just pick the next best rated items from the original scored list.
            if len(recs) < limit - 1:
                current_app.logger.warning(f"Coordination engine only found {len(recs)} matches. Filling with high-score items.")
                existing_ids = set([hero.id] + recs)
                for p, s in scored_heroes:
                    if p.id not in existing_ids:
                        recs.append(p.id)
                        existing_ids.add(p.id)
                    if len(recs) >= limit - 1:
                        break

            return [hero.id] + recs

        except Exception as e:
            current_app.logger.error(f"Set Builder Critical Err: {e}")
            return []

    @staticmethod
    def get_full_outfit(product):
        """
        AI Stylist: Generates a complete 3-piece set from a single item.
        Top + Bottom + Footwear/Outerwear
        """
        recs = OutfitCoordinator.get_recommendations(product, limit=10)
        return [product.id] + recs[:2]

def train_coordination_ai():
    """
    Simulation of 'AI Training' by analyzing inventory trends.
    """
    all_prods = Product.query.all()
    # In a real system, we'd update matrix weights here.
    return {"status": "success", "analyzed_items": len(all_prods), "engine": "Heuristic-Hybrid v3"}

