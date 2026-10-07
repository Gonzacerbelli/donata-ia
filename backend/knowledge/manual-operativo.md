# Manual operativo de Donata

## Descripción general del negocio
Donata es un emprendimiento dedicado a la venta de alfombras, tapices y productos textiles para el hogar. Atiende tanto a clientes minoristas como mayoristas y ofrece servicios adicionales como colocación, corte a medida y confección especial.

## Canales de venta
Se vende de forma presencial en el local, por redes sociales (principalmente Instagram) y por contacto telefónico. Los pedidos de mayoristas suelen acordarse por teléfono y por transferencia bancaria.

## Clientes
Los clientes se clasifican en minoristas, mayoristas o ambos. Un cliente mayorista compra para revender y accede a precios especiales. Un cliente minorista compra para consumo propio. Cuando un cliente es de tipo "ambos", la venta puntual define si se aplica precio mayorista o minorista.

## Productos y categorías
Cada producto tiene un nombre, una categoría, un costo y hasta dos precios: precio minorista y precio mayorista. Los productos pueden tener stock controlado o no. Algunos ítems no son productos con stock, sino servicios: por ejemplo, la colocación de una alfombra se puede cobrar como un ítem descriptivo sin producto asociado.

## Precios
- El precio minorista es el valor de lista para el público general.
- El precio mayorista es un precio más bajo reservado para revendedores.
- Si un producto no tiene precio mayorista cargado, se usa el precio minorista aun para un cliente mayorista.
- El precio de una venta se puede sobrescribir manualmente en el momento de la carga.

## Stock
El stock se descuenta automáticamente al confirmar cada venta y se registra un movimiento por cada cambio. Si el stock no alcanza para cubrir una venta, la operación se rechaza y no se descuenta nada. Al cancelar una venta, el stock de los productos involucrados se restituye. El sistema considera "bajo stock" a todo producto cuyo stock sea menor o igual a su mínimo configurado. Los ajustes manuales de stock se registran con el motivo indicado.

## Ventas
Una venta se compone de clientes y de uno o más ítems. Cada ítem puede ser un producto del catálogo o un servicio descriptivo. La venta admite un descuento por monto fijo o por porcentaje y un costo de envío. El total se calcula como subtotal menos descuento más envío.

### Estados de una venta
- pendiente: la venta fue creada y todavía no se preparó.
- en_proceso: la venta está siendo preparada o en fabricación.
- entregado: la venta fue entregada al cliente.
- cancelado: la venta fue anulada y el stock se restituyó.

## Pagos y saldo
Las ventas pueden tener varios pagos y adelantos. El total pagado es la suma de todos los pagos registrados. El saldo es el total de la venta menos lo pagado. Una venta cancelada no admite nuevos pagos. No se puede eliminar una venta que tenga pagos registrados.

## Cancelaciones y bajas
Cancelar una venta restituye el stock de sus productos. No se pueden eliminar clientes, proveedores o productos que tengan registros asociados: el sistema responde con un conflicto de integridad. Eliminar un hilo de conversación borra también todos sus mensajes.

## Proveedores
Cada producto pertenece a un proveedor. No se puede borrar un proveedor que tenga productos asociados. La compra de mercadería se refleja como un ajuste positivo de stock.

## Reportes y control
El negocio controla la cantidad de ventas, la facturación, lo cobrado y lo que queda por cobrar (saldo). También analiza los productos más vendidos, mide el valor del inventario al costo y vigila los productos con bajo stock para reponerlos.

## Asistente de IA
El asistente de Donata responde únicamente consultas relacionadas con la operación del negocio: productos, precios, stock, clientes, ventas, proveedores y reportes. No responde temas ajenos al negocio. Cuando se solicitan datos concretos, los obtiene consultando las herramientas internas en lugar de inventarlos. Toda respuesta se basa en datos reales del sistema o en este manual operativo.