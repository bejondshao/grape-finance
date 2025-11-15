import codecs  
with codecs.open("src/pages/StockView.jsx", "r", "utf-8") as f:  
    content = f.read()  
with codecs.open("src/pages/StockView_fixed.jsx", "w", "utf-8") as f:  
    f.write(content) 
