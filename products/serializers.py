from rest_framework import serializers
from .models import Product, Category, ProductImage, Review, ProductLike

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    likes_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'thumbnail', 'category', 'average_rating', 'likes_count']

    def get_thumbnail(self, obj):
        thumbnail = obj.images.filter(is_thumbnail=True).first()
        if thumbnail:
            return self.context['request'].build_absolute_uri(thumbnail.image.url)
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    reviews_count = serializers.ReadOnlyField()
    likes_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'images', 'category',
                 'attributes', 'average_rating', 'reviews_count', 'likes_count',
                 'is_liked', 'in_stock', 'created_at', 'updated_at']

    def get_images(self, obj):
        images = obj.images.all()
        return [self.context['request'].build_absolute_uri(img.image.url) for img in images]

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ProductLike.objects.filter(product=obj, user=user).exists()
        return False

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product_id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'product_id', 'user', 'created_at']

    def get_user(self, obj):
        return {'id': obj.user.id, 'name': obj.user.name}

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']