from rest_framework import serializers
from .models import Review, ProductLike
from orders.models import OrderItem


class ReviewUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product_id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

    def validate(self, attrs):
        user = self.context['request'].user
        product_id = self.context['product_id']

        # Check if user has purchased this product
        has_purchased = OrderItem.objects.filter(
            order__user=user,
            product_id=product_id,
            order__status__in=['delivered', 'processing', 'shipped']
        ).exists()

        if not has_purchased:
            raise serializers.ValidationError(
                "You can only review products you have purchased"
            )

        # Check if user already reviewed this product
        if Review.objects.filter(user=user, product_id=product_id).exists():
            raise serializers.ValidationError(
                "You have already reviewed this product"
            )

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product_id = self.context['product_id']

        return Review.objects.create(
            user=user,
            product_id=product_id,
            **validated_data
        )


class ProductLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLike
        fields = ['liked', 'likes_count']

    def to_representation(self, instance):
        # instance is the product here
        user = self.context['request'].user

        if user.is_authenticated:
            liked = ProductLike.objects.filter(user=user, product=instance).exists()
        else:
            liked = False

        return {
            'liked': liked,
            'likes_count': instance.likes.count()
        }