using System.ComponentModel.DataAnnotations;

namespace ProductApi.Models;

public class Product
{
    public int Id { get; set; }

    [Required, StringLength(200)]
    public string Name { get; set; } = string.Empty;

    [StringLength(5000)]
    public string Description { get; set; } = string.Empty;

    [Range(typeof(decimal), "0", "9999999999.99")]
    public decimal Price { get; set; }

    [Range(0, int.MaxValue)]
    public int Stock { get; set; }

    [StringLength(2048)]
    public string ImageUrl { get; set; } = string.Empty;

    [StringLength(100)]
    public string Category { get; set; } = string.Empty;
}
