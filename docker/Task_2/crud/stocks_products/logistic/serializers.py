from rest_framework import serializers

from logistic.models import Product, Stock, StockProduct


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'description']


class ProductPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockProduct
        fields = ['quantity', 'product', 'price']


class StockSerializer(serializers.ModelSerializer):
    positions = ProductPositionSerializer(many=True)

    class Meta:
        model = Stock
        fields = ['id', 'address', 'positions']

    def create(self, validated_data):
        positions = validated_data.pop('positions')
        stock = super().create(validated_data)
        for item in positions:
            StockProduct.objects.create(quantity=item['quantity'], price=item['price'], product_id=item['product'].id,
                                        stock_id=stock.id)
        return stock

    def update(self, instance, validated_data):
        positions = validated_data.pop('positions')
        stock = super().update(instance, validated_data)
        data = StockProduct.objects.filter(stock_id=instance.id)
        if data:
            for item in positions:
                StockProduct.objects.filter(stock_id=instance.id).filter(product_id=item['product'].id).\
                    update(quantity=item['quantity'], price=item['price'], product_id=item['product'].id,
                           stock_id=stock.id)
        else:
            data = Stock.objects.filter(id=instance.id)
            if data:
                for item in positions:
                    StockProduct.objects.create(quantity=item['quantity'], price=item['price'],
                                                product_id=item['product'].id, stock_id=stock.id)
        return stock
