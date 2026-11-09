from rest_framework import serializers
from .models import Purchase, PurchaseLine, Sale, SaleLine, Expense, Payment

class PurchaseLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseLine
        fields = ['item', 'quantity', 'unit', 'unit_price', 'total'] 

class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True)
    payments = serializers.SerializerMethodField()
    payment_method = serializers.CharField(required=False, default='CASH', write_only=True)
    reference = serializers.CharField(required=False, default='', write_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'farm', 'party', 'event_date', 'classification', 
            'total_amount', 'amount_paid', 'outstanding_balance',
            'receipt_status', 'payment_method', 'reference',
            'notes', 'lines', 'payments', 'entry_timestamp', 'created_by'
        ]
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by', 'total_amount', 'outstanding_balance']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}

    def get_payments(self, obj):
        payments = Payment.objects.filter(transaction_type='PURCHASE', transaction_id=obj.id)
        return PaymentSerializer(payments, many=True).data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        amount_paid = validated_data.get('amount_paid', 0)
        payment_method = validated_data.pop('payment_method', 'CASH') 
        reference = validated_data.pop('reference', '')
        
        purchase = Purchase.objects.create(**validated_data)
        
        total_sum = 0
        for line in lines_data:
            if 'total' not in line or line['total'] is None:
                line['total'] = line['quantity'] * line['unit_price']
            PurchaseLine.objects.create(purchase=purchase, **line)
            total_sum += line['total']
            
        purchase.total_amount = total_sum
        purchase.amount_paid = amount_paid
        purchase.outstanding_balance = total_sum - amount_paid
        purchase.save()

        if amount_paid > 0:
            Payment.objects.create(
                farm_id=purchase.farm_id,
                transaction_type='PURCHASE',
                transaction_id=purchase.id,
                amount=amount_paid,
                payment_method=payment_method, 
                reference=reference,
                event_date=purchase.event_date,
                created_by=purchase.created_by,
                notes='Initial payment at purchase creation'
            )

        # --- STOCK LEDGER: PURCHASE (IN) ---
        if purchase.receipt_status == 'RECEIVED':
            from apps.catalog.models import StockMovement, Unit, UnitConversion
            
            for line in purchase.lines.all():
                base_quantity = line.quantity
                if line.unit:
                    try:
                        unit_obj = Unit.objects.get(name__iexact=line.unit)
                        conversion = UnitConversion.objects.get(item=line.item, unit=unit_obj)
                        base_quantity = line.quantity * conversion.factor
                    except (Unit.DoesNotExist, UnitConversion.DoesNotExist):
                        pass 
                
                StockMovement.objects.create(
                    farm_id=purchase.farm_id,
                    item=line.item,
                    direction='IN',
                    quantity=base_quantity,
                    source_type='PURCHASE',
                    source_id=purchase.id,
                    event_date=purchase.event_date,
                    created_by=purchase.created_by,
                    notes=f"Received from purchase #{purchase.id}"
                )
        # ------------------------------------------------

        return purchase


class SaleLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleLine
        fields = ['item', 'quantity', 'unit', 'unit_price', 'total', 'flock']

class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True)
    payments = serializers.SerializerMethodField()
    payment_method = serializers.CharField(required=False, default='CASH', write_only=True)
    reference = serializers.CharField(required=False, default='', write_only=True)
    
    # NEW: Explicitly return the party name for the frontend
    party_name = serializers.CharField(source='party.name', read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'farm', 'party', 'party_name', 'event_date', 'classification', 
            'discount_type', 'discount_value', 'total_amount', 
            'amount_paid', 'outstanding_balance', 'payment_method', 'reference',
            'notes', 'lines', 'payments', 'entry_timestamp', 'created_by'
        ]
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by', 'total_amount', 'outstanding_balance']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}

    def get_payments(self, obj):
        payments = Payment.objects.filter(transaction_type='SALE', transaction_id=obj.id)
        return PaymentSerializer(payments, many=True).data

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        discount_type = validated_data.get('discount_type', 'FIXED')
        discount_value = validated_data.get('discount_value', 0)
        amount_paid = validated_data.get('amount_paid', 0)
        payment_method = validated_data.pop('payment_method', 'CASH')
        reference = validated_data.pop('reference', '')
        
        subtotal = 0
        for line in lines_data:
            if 'total' not in line or line['total'] is None:
                line['total'] = line['quantity'] * line['unit_price']
            subtotal += line['total']
            
        if discount_type == 'PERCENT':
            discount_amount = subtotal * (discount_value / 100)
        else:
            discount_amount = discount_value
            
        final_total = max(0, subtotal - discount_amount)
        
        sale = Sale.objects.create(**validated_data)
        sale.total_amount = final_total
        sale.amount_paid = amount_paid
        sale.outstanding_balance = final_total - amount_paid
        sale.save()

        if amount_paid > 0:
            Payment.objects.create(
                farm_id=sale.farm_id,
                transaction_type='SALE',
                transaction_id=sale.id,
                amount=amount_paid,
                payment_method=payment_method,
                reference=reference,
                event_date=sale.event_date,
                created_by=sale.created_by,
                notes='Initial payment at sale creation'
            )
        
        # Create lines and handle stock/flock logic
        for line in lines_data:
            # DRF has already converted line['item'] into an Item model instance
            sale_line = SaleLine.objects.create(sale=sale, **line)
            
            # --- STOCK LEDGER: SALE (OUT) ---
            from apps.catalog.models import StockMovement, Unit, UnitConversion
            
            base_quantity = line['quantity']
            line_unit = line.get('unit', '')
            line_item = line.get('item') # This is an Item instance, not an ID
            
            if line_unit and line_item:
                try:
                    unit_obj = Unit.objects.filter(name__iexact=line_unit).first()
                    if unit_obj:
                        conversion = UnitConversion.objects.get(item=line_item, unit=unit_obj)
                        base_quantity = line['quantity'] * conversion.factor
                except (Unit.DoesNotExist, UnitConversion.DoesNotExist):
                    pass
            
            if line_item:
                StockMovement.objects.create(
                    farm_id=sale.farm_id,
                    item=line_item, # Pass the Item instance directly
                    direction='OUT',
                    quantity=base_quantity,
                    source_type='SALE',
                    source_id=sale.id,
                    event_date=sale.event_date,
                    created_by=sale.created_by,
                    notes=f"Sold in sale #{sale.id}"
                )
            # ------------------------------------
            
            # Flock logic for selling birds
            flock_id = line.get('flock')
            if flock_id:
                from apps.operations.models import Flock
                try:
                    flock = Flock.objects.get(id=flock_id)
                    if flock.current_count == 0:
                        flock.status = 'Sold out'
                        flock.save()
                except Flock.DoesNotExist:
                    pass
            
        return sale

    def update(self, instance, validated_data):
        """
        When a sale is updated, we need to:
        1. Reverse the old stock movements (add stock back)
        2. Delete the old lines
        3. Create new lines with the updated data
        4. Create new stock movements (subtract stock)
        """
        from apps.catalog.models import StockMovement, Unit, UnitConversion
        from apps.operations.models import Flock

        # 1. Store old line data and reverse their stock movements
        old_lines = list(instance.lines.all())
        for old_line in old_lines:
            base_quantity = old_line.quantity
            if old_line.unit:
                try:
                    unit_obj = Unit.objects.filter(name__iexact=old_line.unit).first()
                    if unit_obj:
                        conversion = UnitConversion.objects.get(item=old_line.item, unit=unit_obj)
                        base_quantity = old_line.quantity * conversion.factor
                except (Unit.DoesNotExist, UnitConversion.DoesNotExist):
                    pass
            
            # Reverse the stock movement (add stock back)
            StockMovement.objects.create(
                farm_id=instance.farm_id,
                item=old_line.item,
                direction='IN',
                quantity=base_quantity,
                source_type='SALE',
                source_id=instance.id,
                event_date=instance.event_date,
                created_by=instance.created_by,
                notes=f"Reversed from sale #{instance.id} adjustment"
            )
            
            # Handle flock logic (if birds were sold, restore the flock count)
            if old_line.flock:
                try:
                    flock = Flock.objects.get(id=old_line.flock_id)
                    # Note: current_count is a computed property, so we don't need to update it
                except Flock.DoesNotExist:
                    pass
            
            # Delete the old line
            old_line.delete()

        # 2. Update basic sale fields
        instance.event_date = validated_data.get('event_date', instance.event_date)
        instance.party = validated_data.get('party', instance.party)
        instance.discount_type = validated_data.get('discount_type', instance.discount_type)
        instance.discount_value = validated_data.get('discount_value', instance.discount_value)
        instance.amount_paid = validated_data.get('amount_paid', instance.amount_paid)
        instance.notes = validated_data.get('notes', instance.notes)
        
        # Recalculate totals
        lines_data = validated_data.pop('lines', None)
        if lines_data:
            subtotal = 0
            for line in lines_data:
                if 'total' not in line or line['total'] is None:
                    line['total'] = line['quantity'] * line['unit_price']
                subtotal += line['total']
            
            discount_type = instance.discount_type
            discount_value = instance.discount_value
            if discount_type == 'PERCENT':
                discount_amount = subtotal * (discount_value / 100)
            else:
                discount_amount = discount_value
                
            final_total = max(0, subtotal - discount_amount)
            instance.total_amount = final_total
            instance.outstanding_balance = final_total - instance.amount_paid
        
        instance.save()

        # 3. Create new lines and stock movements
        if lines_data:
            for line in lines_data:
                sale_line = SaleLine.objects.create(sale=instance, **line)
                
                base_quantity = line['quantity']
                line_unit = line.get('unit', '')
                line_item = line.get('item')
                
                if line_unit and line_item:
                    try:
                        unit_obj = Unit.objects.filter(name__iexact=line_unit).first()
                        if unit_obj:
                            conversion = UnitConversion.objects.get(item=line_item, unit=unit_obj)
                            base_quantity = line['quantity'] * conversion.factor
                    except (Unit.DoesNotExist, UnitConversion.DoesNotExist):
                        pass
                
                if line_item:
                    StockMovement.objects.create(
                        farm_id=instance.farm_id,
                        item=line_item,
                        direction='OUT',
                        quantity=base_quantity,
                        source_type='SALE',
                        source_id=instance.id,
                        event_date=instance.event_date,
                        created_by=instance.created_by,
                        notes=f"Updated sale #{instance.id}"
                    )
                
                # Handle flock logic for selling birds
                flock_id = line.get('flock')
                if flock_id:
                    try:
                        flock = Flock.objects.get(id=flock_id)
                        if flock.current_count == 0:
                            flock.status = 'Sold out'
                            flock.save()
                    except Flock.DoesNotExist:
                        pass

        return instance


class ExpenseSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    payments = serializers.SerializerMethodField()
    payment_method = serializers.CharField(required=False, default='CASH', write_only=True)
    reference = serializers.CharField(required=False, default='', write_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'farm', 'party', 'category', 'amount', 'event_date', 'classification', 
            'amount_paid', 'outstanding_balance', 'payment_method', 'reference',
            'notes', 'payments', 'entry_timestamp', 'created_by'
        ]
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by', 'outstanding_balance']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}

    def get_payments(self, obj):
        payments = Payment.objects.filter(transaction_type='EXPENSE', transaction_id=obj.id)
        return PaymentSerializer(payments, many=True).data

    def create(self, validated_data):
        amount_paid = validated_data.get('amount_paid', 0)
        payment_method = validated_data.pop('payment_method', 'CASH')
        reference = validated_data.pop('reference', '')
        
        expense = Expense.objects.create(**validated_data)
        expense.amount_paid = amount_paid
        expense.outstanding_balance = expense.amount - amount_paid
        expense.save()

        if amount_paid > 0:
            Payment.objects.create(
                farm_id=expense.farm_id,
                transaction_type='EXPENSE',
                transaction_id=expense.id,
                amount=amount_paid,
                payment_method=payment_method,
                reference=reference,
                event_date=expense.event_date,
                created_by=expense.created_by,
                notes='Initial payment at expense creation'
            )

        return expense


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_type', 'transaction_id', 'amount', 
            'payment_method', 'reference', 'notes', 'event_date', 
            'entry_timestamp', 'created_by'
        ]
        read_only_fields = ['entry_timestamp', 'created_by']

    def create(self, validated_data):
        payment = Payment.objects.create(**validated_data)
        
        t_type = validated_data.get('transaction_type')
        t_id = validated_data.get('transaction_id')
        amount = validated_data.get('amount')

        if t_type == 'SALE':
            try:
                sale = Sale.objects.get(id=t_id)
                sale.amount_paid += amount
                sale.outstanding_balance = sale.total_amount - sale.amount_paid
                sale.save()
            except Sale.DoesNotExist:
                pass
        elif t_type == 'PURCHASE':
            try:
                purchase = Purchase.objects.get(id=t_id)
                purchase.amount_paid += amount
                purchase.outstanding_balance = purchase.total_amount - purchase.amount_paid
                purchase.save()
            except Purchase.DoesNotExist:
                pass
        elif t_type == 'EXPENSE':
            try:
                expense = Expense.objects.get(id=t_id)
                expense.amount_paid += amount
                expense.outstanding_balance = expense.amount - expense.amount_paid
                expense.save()
            except Expense.DoesNotExist:
                pass
                
        return payment