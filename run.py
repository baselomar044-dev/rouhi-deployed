#!/usr/bin/env python3
"""
🚀 سكريبت تشغيل روحي
يقوم بتثبيت المتطلبات وتشغيل التطبيق تلقائياً
"""

import subprocess
import sys
import os

def install_requirements():
    """تثبيت المتطلبات"""
    print("📦 جاري تثبيت المتطلبات...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "flask", "openai"])
        print("✅ تم تثبيت المتطلبات")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ فشل تثبيت المتطلبات، جاري المحاولة بطريقة أخرى...")
        return False

def main():
    print("""
    ╔═══════════════════════════════════════╗
    ║     💜 روحي - Rouhi AI 💜            ║
    ║   رفقاء ذكاء اصطناعي بعمق إنساني     ║
    ╚═══════════════════════════════════════╝
    """)
    
    # التأكد من المتطلبات
    try:
        import flask
        import openai
    except ImportError:
        if not install_requirements():
            print("❌ لم نتمكن من تثبيت المتطلبات")
            print("   جرب: pip install flask openai")
            sys.exit(1)
    
    # التبديل للمجلد الصحيح
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # استيراد وتشغيل التطبيق
    print("🚀 جاري تشغيل التطبيق...")
    print("")
    
    import app
    app.init_db()
    app.seed_characters()
    
    print("")
    print("═" * 50)
    print("✅ التطبيق يعمل الآن!")
    print("")
    print("🌐 افتح المتصفح على: http://localhost:5000")
    print("")
    print("💡 نصائح:")
    print("   • أضف مفتاح OpenAI من الإعدادات للحصول على ردود AI حقيقية")
    print("   • بدون المفتاح، ستحصل على ردود احتياطية بسيطة")
    print("")
    print("🛑 لإيقاف التطبيق: Ctrl+C")
    print("═" * 50)
    print("")
    
    app.app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
