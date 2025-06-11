from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

class Color(BaseModel):
    r: float; g: float; b: float; a: float

class Paint(BaseModel):
    blendMode: Optional[str] = None
    type:      Optional[str] = None
    color:     Optional[Color] = None

class Rectangle(BaseModel):
    x: float; y: float; width: float; height: float

class Constraints(BaseModel):
    vertical:   Optional[str] = None
    horizontal: Optional[str] = None

class Effect(BaseModel):
    type: Literal["DROP_SHADOW", "INNER_SHADOW", "LAYER_BLUR", "BACKGROUND_BLUR"]
    visible: Optional[bool] = Field(default=True)
    blendMode: Optional[str] = None

    # For shadow types:
    color: Optional[Color] = None
    offset: Optional[Dict[str, float]] = None   # e.g. {"x":5, "y":5}
    radius: Optional[float] = None              # blur radius
    spread: Optional[float] = None              # for DROP_SHADOW only

    # For blur types, only `radius` is used

    # catch all for any extra props
    additionalProperties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"

class Interaction(BaseModel):
    type: Optional[str] = None

class TargetAspectRatio(BaseModel):
    x: float; y: float

class TextStyle(BaseModel):
    fontFamily:           Optional[str] = None
    fontPostScriptName:   Optional[str] = None
    fontStyle:            Optional[str] = None
    fontWeight:           Optional[float] = None
    textAutoResize:       Optional[str] = None
    fontSize:             Optional[float] = None
    textAlignHorizontal:  Optional[str] = None
    textAlignVertical:    Optional[str] = None
    letterSpacing:        Optional[float] = None
    lineHeightPx:         Optional[float] = None
    lineHeightPercent:    Optional[float] = None
    lineHeightUnit:       Optional[str] = None

class FrameNode(BaseModel):
    id: str
    name: Optional[str]
    type: Literal["FRAME"]

    # layout & auto-layout
    scrollBehavior:          Optional[str] = None
    blendMode:               Optional[str] = None
    clipsContent:            Optional[bool] = None
    layoutMode:              Optional[Literal["HORIZONTAL","VERTICAL"]] = None
    itemSpacing:             Optional[float] = None
    primaryAxisSizingMode:   Optional[str] = None
    counterAxisAlignItems:   Optional[str] = None
    layoutGrow:              Optional[float] = None
    layoutAlign:             Optional[str] = None
    layoutWrap:              Optional[str] = None
    layoutSizingHorizontal:  Optional[str] = None
    layoutSizingVertical:    Optional[str] = None

    # spacing
    paddingTop:    Optional[float] = None
    paddingRight:  Optional[float] = None
    paddingBottom: Optional[float] = None
    paddingLeft:   Optional[float] = None

    # size & position
    absoluteBoundingBox:  Optional[Rectangle] = None
    absoluteRenderBounds: Optional[Rectangle] = None
    constraints:          Optional[Constraints] = None

    # styling
    background:     Optional[List[Paint]] = None
    fills:          Optional[List[Paint]] = Field(default_factory=list)
    strokes:        Optional[List[Paint]] = Field(default_factory=list)
    strokeWeight:   Optional[float] = 0.0
    strokeAlign:    Optional[str] = None
    backgroundColor: Optional[Color] = None

    # corners
    cornerRadius:            Optional[float] = None
    rectangleCornerRadii:    Optional[List[float]] = None
    cornerSmoothing:         Optional[float] = None

    # effects & interactivity
    effects: List[Effect] = Field(default_factory=list)
    interactions: Optional[List[Interaction]] = None

    # recursive children of any node type
    children: Optional[List[Union[FrameNode, TextNode, VectorNode]]] = None

    # misc
    layoutVersion: Optional[int] = None
    additionalProperties: Dict[str, Any] = {}

    class Config:
        extra = "allow"

class TextNode(BaseModel):
    id: str
    name: Optional[str]
    type: Literal["TEXT"]
    characters: Optional[str]
    characterStyleOverrides: Optional[List[int]] = None
    styleOverrideTable:      Optional[Dict[str, Any]] = None
    lineTypes:               Optional[List[str]] = None
    lineIndentations:        Optional[List[float]] = None
    style:                   Optional[TextStyle] = None
    fills:                   Optional[List[Paint]] = None
    strokes:                 Optional[List[Paint]] = None
    strokeWeight:            Optional[float] = None
    strokeAlign:             Optional[str] = None
    absoluteBoundingBox:     Optional[Rectangle] = None
    absoluteRenderBounds:    Optional[Rectangle] = None
    constraints:             Optional[Constraints] = None
    layoutAlign:             Optional[str] = None
    layoutGrow:              Optional[float] = None
    layoutSizingHorizontal:  Optional[str] = None
    layoutSizingVertical:    Optional[str] = None
    blendMode:               Optional[str] = None
    scrollBehavior:          Optional[str] = None
    effects:                 List[Effect] = Field(default_factory=list)
    interactions:            Optional[List[Interaction]] = None
    additionalProperties:    Dict[str, Any] = {}

    class Config:
        extra = "allow"

class VectorNode(BaseModel):
    id: str
    name: Optional[str] = None
    type: Literal["VECTOR"]
    scrollBehavior: Optional[str] = None
    blendMode:      Optional[str] = None
    fills:          Optional[List[Paint]] = None
    strokes:        Optional[List[Paint]] = None
    strokeWeight:   Optional[float] = None
    strokeAlign:    Optional[str] = None
    absoluteBoundingBox:   Optional[Rectangle] = None
    absoluteRenderBounds:  Optional[Rectangle] = None
    constraints:           Optional[Constraints] = None
    layoutAlign:           Optional[str] = None
    layoutGrow:            Optional[float] = None
    layoutSizingHorizontal:Optional[str] = None
    layoutSizingVertical:  Optional[str] = None
    targetAspectRatio:     Optional[TargetAspectRatio] = None
    effects: List[Effect] = Field(default_factory=list)
    interactions: Optional[List[Interaction]] = None
    additionalProperties: Dict[str, Any] = {}

    class Config:
        extra = "allow"
