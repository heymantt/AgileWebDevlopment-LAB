from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

receipts_bp = Blueprint("receipts", __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@receipts_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_receipt():
    if request.method == "POST":
        try:
            # Get form data
            amount = request.form.get("amount", "0")
            category = request.form.get("category", "other")
            merchant = request.form.get("merchant", "")
            description = request.form.get("description", "")
            
            # Validate amount
            try:
                amount_value = float(amount)
                if amount_value <= 0:
                    flash("Amount must be greater than 0.", "error")
                    return redirect(url_for("receipts.upload_receipt"))
            except ValueError:
                flash("Invalid amount entered.", "error")
                return redirect(url_for("receipts.upload_receipt"))
            
            # File upload is optional
            filename = None
            if "file" in request.files:
                file = request.files["file"]
                if file and file.filename != "":
                    if not allowed_file(file.filename):
                        flash("Invalid file type. Only PNG, JPG, JPEG, GIF, and PDF files are allowed.", "error")
                        return redirect(url_for("receipts.upload_receipt"))
                    
                    # Create uploads directory if it doesn't exist
                    upload_folder = os.path.join("app", "static", "uploads", "receipts")
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                    filename = secure_filename(timestamp + file.filename)
                    
                    # Save file
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
            
            flash(f"✓ Receipt recorded successfully! Amount: ${amount_value:.2f} ({category})", "success")
            return redirect(url_for("receipts.archive"))
            
        except Exception as e:
            flash(f"Error uploading receipt: {str(e)}", "error")
            return redirect(url_for("receipts.upload_receipt"))
    
    return render_template("receipts/upload.html", page_title="Upload Receipt")




@receipts_bp.route("/archive")
@login_required
def archive():
    # Get list of uploaded receipts
    upload_folder = os.path.join("app", "static", "uploads", "receipts")
    receipts = []
    
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                receipts.append({
                    'filename': filename,
                    'size': f"{file_size / 1024:.2f} KB",
                    'date': datetime.fromtimestamp(file_time).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    # Sort by date (newest first)
    receipts.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template(
        "receipts/archive.html", 
        page_title="Receipt Archive",
        receipts=receipts
    )


@receipts_bp.route("/<int:receipt_id>")
@login_required
def receipt_detail(receipt_id):
    return render_template(
        "receipts/detail.html",
        page_title="Receipt Detail",
        heading=f"Receipt Detail #{receipt_id}"
    )